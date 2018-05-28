# -*- coding: utf-8 -*-
import json
import re
import subprocess
import sys
import time
import glob

import os
from os.path import join, split, dirname, basename, abspath
from traitlets import Unicode

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec

CACHE_TIMEOUT = 60

CONDA_EXE = os.environ.get("CONDA_EXE", "conda")


class CondaKernelSpecManager(KernelSpecManager):
    """ A custom KernelSpecManager able to search for conda environments and
        create kernelspecs for them.
    """
    env_filter = Unicode(None, config=True, allow_none=True,
                         help="Do not list environment names that match this regex")

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
                p = subprocess.check_output([CONDA_EXE, "info", "--json"],
                                            shell=shell).decode("utf-8")
                conda_info = json.loads(p)
            except Exception as err:
                conda_info = None
                self.log.error("[nb_conda_kernels] couldn't call conda:\n%s",
                               err)
            self._conda_info_cache = conda_info
            self._conda_info_cache_expiry = time.time() + CACHE_TIMEOUT

        return self._conda_info_cache

    def _skip_env(self, path):
        """Get whether the environment should be included in the kernel specs or
        not based on whether its path matches env_filter.

        If the filter regex is None, always returns False (i.e., never skips).

        Parameters
        ----------
        path: str
            Full path of the conda environment

        Returns
        -------
        bool
            True if the filter matches and the env should not be included in
            the kernel specs.
        """
        if self.env_filter is None:
            return False
        return self._env_filter_regex.search(path) is not None

    def _all_envs(self):
        """ Find all of the environments we should be checking. We do not
            include the current environment, since Jupyter is already
            picking that up, nor do we include environments that match
            the env_filter regex. Returns a dict with canonical environment
            names as keys, and full paths as values.
        """
        conda_info = self._conda_info
        base_prefix = conda_info['conda_prefix']
        envs_dirs = conda_info['envs_dirs']
        conda_version = float(conda_info['conda_version'].rsplit('.', 1)[0])
        all_envs = {}
        for env_path in conda_info['envs']:
            if self._skip_env(env_path):
                continue
            elif env_path == sys.prefix:
                continue
            elif env_path == base_prefix:
                env_name = 'root' if conda_version < 4.4 else 'base'
            else:
                env_base, env_name = split(env_path)
                if env_base not in envs_dirs or env_name in all_envs:
                    env_name = env_path
            all_envs[env_name] = env_path
        return all_envs

    def _all_specs(self):
        """ Find the all kernel specs in all environments besides sys.prefix.

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
        for env_name, env_path in self._all_envs().items():
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
                kernel_dir = dirname(spec_path)
                kernel_name = 'conda-env-{}-{}'.format(
                    basename(env_name), basename(kernel_dir))
                # Just in case there are multiple environments with the
                # same basename, we'll do a simple disambiguation
                while kernel_name in all_specs:
                    kernel_name += '-'
                spec['display_name'] += ' [conda env: {}]'.format(env_name)
                spec['argv'] = ['nb-conda-run', conda_prefix, env_path] + spec['argv']
                spec['resource_dir'] = abspath(kernel_dir)
                all_specs[kernel_name] = spec
        return all_specs

    @property
    def _conda_kspecs(self):
        """ Get (or refresh) the cache of conda kernels
        """
        if self._conda_info is None:
            return {}

        if (self._conda_kernels_cache_expiry is None or
            self._conda_kernels_cache_expiry < time.time()):
            self.log.debug("[nb_conda_kernels] refreshing conda kernelspecs")
            self._conda_kernels_cache = self._load_conda_kspecs()
            self._conda_kernels_cache_expiry = time.time() + CACHE_TIMEOUT

        return self._conda_kernels_cache

    def _load_conda_kspecs(self):
        """ Create a kernelspec for each of the envs where jupyter is installed
        """
        kspecs = {}
        for name, info in self._all_specs().items():
            kspecs[name] = KernelSpec(**info)
        return kspecs

    def find_kernel_specs(self):
        """ Returns a dict mapping kernel names to resource directories.

            The update process also adds the resource dir for the conda
            environments.
        """
        kspecs = super(CondaKernelSpecManager, self).find_kernel_specs()

        # add conda envs kernelspecs
        kspecs.update({name: spec.resource_dir
                       for name, spec
                       in self._conda_kspecs.items()})
        return kspecs

    def get_kernel_spec(self, kernel_name):
        """ Returns a :class:`KernelSpec` instance for the given kernel_name.

            Additionally, conda kernelspecs are generated on the fly
            accordingly with the detected envitonments.
        """

        return (
            self._conda_kspecs.get(kernel_name) or
            super(CondaKernelSpecManager, self).get_kernel_spec(kernel_name)
        )
