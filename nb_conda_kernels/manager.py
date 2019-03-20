# -*- coding: utf-8 -*-
import json
import re
import subprocess
import sys
import time
import glob

import os
from os.path import join, split, dirname, basename, abspath
from traitlets import Unicode, Bool

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec, NoSuchKernel

CACHE_TIMEOUT = 60

CONDA_EXE = os.environ.get("CONDA_EXE", "conda")

RUNNER_COMMAND = ['python', '-m', 'nb_conda_kernels.runner']


class CondaKernelSpecManager(KernelSpecManager):
    """ A custom KernelSpecManager able to search for conda environments and
        create kernelspecs for them.
    """
    conda_only = Bool(False,
                      help="Include only the kernels not visible from Jupyter normally")

    env_filter = Unicode(None, config=True, allow_none=True,
                         help="Do not list environment names that match this regex")

    name_format = Unicode('{0} [conda env:{1}]', config=True,
                          help="String name format; '{{0}}' = Language, '{{1}}' = Kernel")

    def __init__(self, **kwargs):
        super(CondaKernelSpecManager, self).__init__(**kwargs)

        self._conda_info_cache = None
        self._conda_info_cache_expiry = None

        self._conda_kernels_cache = None
        self._conda_kernels_cache_expiry = None

        if self.env_filter is not None:
            self._env_filter_regex = re.compile(self.env_filter)

        self.log.info("[nb_conda_kernels] enabled, %s kernels found",
                      len(self._conda_kspecs))

    @staticmethod
    def clean_kernel_name(kname):
        """ Replaces invalid characters in the Jupyter kernelname, with
            a bit of effort to preserve readability.
        """
        try:
            kname.encode('ascii')
        except UnicodeEncodeError:
            # Replace accented characters with unaccented equivalents
            import unicodedata
            nfkd_form = unicodedata.normalize('NFKD', kname)
            kname = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
        # Replace anything else, including spaces, with underscores
        kname = re.sub('[^a-zA-Z0-9._\-]', '_', kname)
        return kname

    @property
    def _conda_info(self):
        """ Get and parse the whole conda information output

            Caches the information for CACHE_TIMEOUT seconds, as this is
            relatively expensive.
        """

        expiry = self._conda_info_cache_expiry
        if expiry is None or expiry < time.time():
            self.log.debug("[nb_conda_kernels] refreshing conda info")
            # This is to make sure that subprocess can find 'conda' even if
            # it is a Windows batch file---which is the case in non-root
            # conda environments.
            shell = CONDA_EXE == 'conda' and sys.platform.startswith('win')
            try:
                # conda info --json uses the standard JSON escaping
                # mechanism for non-ASCII characters. So it is always
                # valid to decode here as 'ascii', since the JSON loads()
                # method will recover any original Unicode for us.
                p = subprocess.check_output([CONDA_EXE, "info", "--json"],
                                            shell=shell).decode('ascii')
                conda_info = json.loads(p)
            except Exception as err:
                conda_info = None
                self.log.error("[nb_conda_kernels] couldn't call conda:\n%s",
                               err)
            self._conda_info_cache = conda_info
            self._conda_info_cache_expiry = time.time() + CACHE_TIMEOUT

        return self._conda_info_cache

    def _all_envs(self):
        """ Find all of the environments we should be checking. We do not
            include the current environment, since Jupyter is already
            picking that up, nor do we include environments that match
            the env_filter regex. Returns a dict with canonical environment
            names as keys, and full paths as values.
        """
        conda_info = self._conda_info
        envs = conda_info['envs']
        base_prefix = conda_info['conda_prefix']
        build_prefix = join(base_prefix, 'conda-bld')
        # Older versions of conda do not seem to include the base prefix
        # in the environment list, but we do want to scan that
        if base_prefix not in envs:
            envs.insert(0, base_prefix)
        envs_dirs = conda_info['envs_dirs']
        if not envs_dirs:
            envs_dirs = [join(base_prefix, 'envs')]
        all_envs = {}
        for env_path in envs:
            if self.env_filter is not None:
                if self._env_filter_regex.search(env_path):
                    continue
            if env_path == base_prefix:
                env_name = 'root'
            else:
                env_base, env_name = split(env_path)
                if env_base == build_prefix:
                    continue
                if env_base != base_prefix or env_name in all_envs:
                    # Add a prefix to environments not found in the default
                    # environment location. We either use the name of the
                    # parent directory, or the grandparent if the parent
                    # has the name 'envs'. This handles scenarios like multiple
                    # conda installations, anaconda-project instances, etc.
                    env_base, project_name = split(env_base)
                    if project_name == 'envs':
                        project_name = basename(env_base)
                    env_name = u'{}-{}'.format(project_name, env_name)
            # Further disambiguate, if necessary, with a counter.
            if env_name in all_envs:
                base_name = env_name
                for count in range(len(all_envs)):
                    env_name = u'{}-{}'.format(base_name, count + 2)
                    if env_name not in all_envs:
                        break
            all_envs[env_name] = env_path
        return all_envs

    def _all_specs(self):
        """ Find the all kernel specs in all environments.

            Returns a dict with unique env names as keys, and the kernel.json
            content as values, modified so that they can be run properly in
            their native environments.

            Caches the information for CACHE_TIMEOUT seconds, as this is
            relatively expensive.
        """

        all_specs = {}
        # We need to be able to find conda-run in the base conda environment
        # even if this package is not running there
        conda_prefix = self._conda_info['conda_prefix']
        all_envs = self._all_envs()
        for env_name, env_path in all_envs.items():
            kspec_base = join(env_path, 'share', 'jupyter', 'kernels')
            kspec_glob = glob.glob(join(kspec_base, '*', 'kernel.json'))
            for spec_path in kspec_glob:
                try:
                    with open(spec_path) as fp:
                        spec = json.load(fp)
                except Exception as err:
                    self.log.error("[nb_conda_kernels] error loading %s:\n%s",
                                   spec_path, err)
                    continue
                kernel_dir = dirname(spec_path).lower()
                kernel_name = basename(kernel_dir)
                # We're doing a few of these adjustments here to ensure that
                # the naming convention is as close as possible to the previous
                # versions of this package; particularly so that the tests
                # pass without change.
                if kernel_name in ('python2', 'python3'):
                    kernel_name = 'py'
                elif kernel_name == 'ir':
                    kernel_name = 'r'
                kernel_prefix = '' if env_name == 'root' else 'env-'
                kernel_name = u'conda-{}{}-{}'.format(kernel_prefix, env_name, kernel_name)
                # Replace invalid characters with dashes
                kernel_name = self.clean_kernel_name(kernel_name)
                display_prefix = spec['display_name']
                if display_prefix.startswith('Python'):
                    display_prefix = 'Python'
                display_name = self.name_format.format(display_prefix, env_name)
                if env_path == sys.prefix:
                    display_name += ' *'
                spec['display_name'] = display_name
                if env_path != sys.prefix:
                    spec['argv'] = RUNNER_COMMAND + [conda_prefix, env_path] + spec['argv']
                spec['resource_dir'] = abspath(kernel_dir)
                all_specs[kernel_name] = spec
        return all_specs

    @property
    def _conda_kspecs(self):
        """ Get (or refresh) the cache of conda kernels
        """
        if self._conda_info is None:
            return {}

        expiry = self._conda_kernels_cache_expiry
        if expiry is not None and expiry >= time.time():
            return self._conda_kernels_cache

        kspecs = {}
        for name, info in self._all_specs().items():
            kspecs[name] = KernelSpec(**info)

        self._conda_kernels_cache_expiry = time.time() + CACHE_TIMEOUT
        self._conda_kernels_cache = kspecs
        return kspecs

    def find_kernel_specs(self, skip_base=False):
        """ Returns a dict mapping kernel names to resource directories.

            The update process also adds the resource dir for the conda
            environments.
        """
        if self.conda_only:
            kspecs = {}
        else:
            kspecs = super(CondaKernelSpecManager, self).find_kernel_specs()

        # add conda envs kernelspecs
        if self.whitelist:
            kspecs.update({name: spec.resource_dir
                           for name, spec in self._conda_kspecs.items() if name in self.whitelist})
        else:
            kspecs.update({name: spec.resource_dir
                           for name, spec in self._conda_kspecs.items()})
        return kspecs

    def get_kernel_spec(self, kernel_name):
        """ Returns a :class:`KernelSpec` instance for the given kernel_name.

            Additionally, conda kernelspecs are generated on the fly
            accordingly with the detected envitonments.
        """

        res = self._conda_kspecs.get(kernel_name)
        if res is None and not self.conda_only:
            res = super(CondaKernelSpecManager, self).get_kernel_spec(kernel_name)
        return res

    def get_all_specs(self):
        """ Returns a dict mapping kernel names to dictionaries with two
            entries: "resource_dir" and "spec". This was added to fill out
            the full public interface to KernelManagerSpec.
        """
        res = {}
        for name, resource_dir in self.find_kernel_specs().items():
            try:
                spec = self.get_kernel_spec(name)
                res[name] = {'resource_dir': resource_dir,
                             'spec': spec.to_dict()}
            except NoSuchKernel:
                self.log.warning("Error loading kernelspec %r", name, exc_info=True)
        return res
