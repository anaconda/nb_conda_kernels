# -*- coding: utf-8 -*-
import json
import re
import shutil
import subprocess
import threading
import sys
import time
import glob
import psutil

import os
from os.path import join, split, dirname, basename, abspath, exists
from traitlets import Bool, Unicode, TraitError, validate

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec, NoSuchKernel

CACHE_TIMEOUT = 60

RUNNER_COMMAND = ['python', '-m', 'nb_conda_kernels.runner']

_canonical_paths = {}

CONDA_EXE = None


def _conda_exe():
    global CONDA_EXE
    if CONDA_EXE is not None:
        return CONDA_EXE
    for evar in ("CONDA_EXE", "MAMBA_EXE"):
        CONDA_EXE = os.environ.get(evar)
        if CONDA_EXE and exists(CONDA_EXE):
            return CONDA_EXE
    paths = os.environ.get("PATH").split(os.pathsep)
    ext = ".exe" if sys.platform.startswith('win') else ""
    for pname in ("conda", "mamba", "micromamba"):
        for pdir in paths:
            CONDA_EXE = join(pdir, pname + ext)
            if exists(CONDA_EXE):
                return CONDA_EXE
    CONDA_EXE = ""
    return CONDA_EXE


def _canonicalize(path):
    """
    On case-sensitive filesystems, return the path unchanged.
    On case-insensitive filesystems, cache the first value of
    the path that we encounter, and return that for any other
    case variation.
    """
    def _inode(p):
        try:
            return os.stat(p).st_ino
        except FileNotFoundError:
            return -1
    inode1 = _inode(path)
    plower = path.lower()
    inode2 = _inode(plower)
    if inode1 != inode2:
        return path
    inode3 = _inode(path.upper())
    if inode3 != inode2:
        return path
    return _canonical_paths.setdefault(plower, path)


class CondaKernelSpecManager(KernelSpecManager):
    """ A custom KernelSpecManager able to search for conda environments and
        create kernelspecs for them.
    """
    base_name = Unicode("base", config=True,
                        help="The name to give the base/root environment. "
                        "The default is 'base', mirroring conda's naming convention. "
                        "Historically, 'root' was used as well.")
    conda_only = Bool(False, config=True,
                      help="Include only the kernels not visible from Jupyter normally. If False, any "
                      "duplication will be resolved in favor of nb_conda_kernels. This is assumed to "
                      "be true if kernelspec_path is supplied as well.")
    env_filter = Unicode(None, config=True, allow_none=True,
                         help="Exclude kernels from environments that match this regex.")
    kernelspec_path = Unicode(None, config=True, allow_none=True,
        help="""Path to install conda kernel specs to.

        The acceptable values are:
        - ``""`` (empty string): Install for all users
        - ``--user``: Install for the current user instead of system-wide
        - ``--sys-prefix``: Install to Python's sys.prefix
        - ``PREFIX``: Specify an install prefix for the kernelspec. The kernel specs will be
        written in ``PREFIX/share/jupyter/kernels``. Be careful that the PREFIX
        may not be discoverable by Jupyter; set JUPYTER_DATA_DIR to force it or run
        ``jupyter --paths`` to get the list of data directories.

        If None, the conda kernel specs will only be available dynamically on notebook editors.
        """)
    enable_debugger = Bool(None, config=True, allow_none=True,
                           help="Optional: Override debugger setting in kernelspec metadata. "
                           "If this parameter is unset it will default to the source kernel metadata.")

    @validate("kernelspec_path")
    def _validate_kernelspec_path(self, proposal):
        new_value = proposal["value"]
        if new_value is not None:
            if new_value not in ("", "--user", "--sys-prefix"):
                if not os.path.isdir(self.kernelspec_path):
                    raise TraitError("CondaKernelSpecManager.kernelspec_path is not a directory.")
            self.log.debug("nb_conda_kernels | Force conda_only=True as kernelspec_path is not None.")
            self.conda_only = True

        return new_value

    name_format = Unicode(
        '{language} [conda env:{environment}]',
        config=True,
        help="""String name format; available field names within the string:
        '{0}' = Language
        '{1}' = Environment name
        '{conda_kernel}' = Dynamically built kernel name for conda environment
        '{display_name}' = Kernel displayed name (as defined in the kernel spec)
        '{environment}'  = Environment name (identical to '{1}')
        '{kernel}' = Original kernel name (name of the folder containing the kernel spec)
        '{language}'  = Language (identical to '{0}')
        """
    )

    def __init__(self, **kwargs):
        super(CondaKernelSpecManager, self).__init__(**kwargs)

        self._conda_info_cache = None
        self._conda_info_cache_expiry = None
        self._conda_info_cache_thread = None

        self._conda_kernels_cache = None
        self._conda_kernels_cache_expiry = None

        if self.env_filter is not None:
            self._env_filter_regex = re.compile(self.env_filter)

        self._kernel_user = self.kernelspec_path == "--user"
        self._kernel_prefix = None
        if not self._kernel_user:
            self._kernel_prefix = sys.prefix if self.kernelspec_path == "--sys-prefix" else self.kernelspec_path

        self.log.info("nb_conda_kernels | %d kernels found.", len(self._conda_kspecs))

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
        kname = re.sub(r'[^a-zA-Z0-9._\-]', '_', kname)
        return kname

    @property
    def _conda_info(self):
        """ Get and parse the whole conda information output

            Caches the information for CACHE_TIMEOUT seconds, as this is
            relatively expensive.
        """

        def get_conda_info_data():
            global CONDA_EXE
            first_log = CONDA_EXE is None
            conda_exe = _conda_exe()

            if not first_log:
                msg = None
            elif conda_exe:
                msg = "enabled: " + conda_exe
            else:
                msg = "could not find conda or mamba"
            if not conda_exe:
                return None, msg

            try:
               # Let json do the decoding for non-ASCII characters
               out = subprocess.check_output([conda_exe, "info", "--json"])
               conda_info = json.loads(out)
               if 'envs' not in conda_info:
                   # Micromamba does not include the envs list by default
                   out = subprocess.check_output([conda_exe, "env", "list", "--json"])
                   conda_info.update(json.loads(out))
            except Exception as err:
                msg = "error reading conda info: " + str(err)
                return None, msg

            finally:
               self.wait_for_child_processes_cleanup()

            # We moved the post-processing here so we can handle the conda/micromamba
            # differences in one place
            envs = list(map(_canonicalize, conda_info.get('envs') or ()))
            base_prefix = _canonicalize(conda_info.get('conda_prefix') or conda_info.get('base environment'))
            if base_prefix not in envs:
                # Older versions of conda do not include base_prefix in the env list
                envs.insert(0, base_prefix)

            return (base_prefix, envs), msg

        class CondaInfoThread(threading.Thread):
            def run(self):
              self.out, self.err = get_conda_info_data()

        expiry = self._conda_info_cache_expiry
        t = self._conda_info_cache_thread

        # cache is empty
        msg, level = None, "debug"
        if expiry is None:
            conda_info, msg = get_conda_info_data()
            if msg:
                level = "info" if conda_info else "error"
            else:
                msg = "refreshing conda info (blocking call)"
            self._conda_info_cache = conda_info
            self._conda_info_cache_expiry = time.time() + CACHE_TIMEOUT

        # subprocess just finished
        elif t and not t.is_alive():
            t.join()
            conda_info, msg = t.out
            if msg:
                level = "info" if conda_info else "error"
            else:
                msg = "collected conda info (async call)"
            self._conda_info_cache = conda_info
            self._conda_info_cache_expiry = time.time() + CACHE_TIMEOUT
            self._conda_info_cache_thread = None

        # cache expired
        elif not t and expiry < time.time():
            msg = "refreshing conda info (async call)"
            t = CondaInfoThread()
            t.start()
            self._conda_info_cache_thread = t

        if msg:
            getattr(self.log, level)("nb_conda_kernels | %s", msg)

        # else, just return cache
        return self._conda_info_cache

    def _all_envs(self):
        """ Find all of the environments we should be checking. We skip
            environments in the conda-bld directory. Returns a dict with
            canonical environment names as keys, and full paths as values.
        """
        base_prefix, envs = self._conda_info
        if not envs:
            return {}
        envs_prefix = join(base_prefix, 'envs')
        build_prefix = join(base_prefix, 'conda-bld', '')
        all_envs = {}
        for env_path in envs:
            if self.env_filter and self._env_filter_regex.search(env_path):
                continue
            elif env_path == base_prefix:
                env_name = self.base_name
            elif env_path.startswith(build_prefix):
                # Skip the conda-bld directory entirely
                continue
            else:
                env_base, env_name = split(env_path)
                # Add a prefix to environments not found in the default
                # environment location. The assumed convention is that a
                # directory named 'envs' is a collection of environments
                # as created by, say, conda or anaconda-project. The name
                # of the parent directory, then, provides useful context.
                if basename(env_base) == 'envs' and (env_base != envs_prefix or env_name in all_envs):
                    env_name = u'{}-{}'.format(basename(dirname(env_base)), env_name)
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
        conda_prefix, _ = self._conda_info
        all_envs = self._all_envs()
        for env_name, env_path in all_envs.items():
            kspec_base = join(env_path, 'share', 'jupyter', 'kernels')
            kspec_glob = glob.glob(join(kspec_base, '*', 'kernel.json'))
            for spec_path in kspec_glob:
                try:
                    with open(spec_path, 'rb') as fp:
                        data = fp.read()
                    spec = json.loads(data.decode('utf-8'))
                except Exception as err:
                    self.log.error("nb_conda_kernels | error loading %s:\n%s",
                                   spec_path, err)
                    continue
                kernel_dir = dirname(spec_path)
                kernel_name = raw_kernel_name = basename(kernel_dir)
                if self.kernelspec_path is not None and kernel_name.startswith("conda-"):
                    self.log.debug("nb_conda_kernels | Skipping kernel spec %s", spec_path)
                    continue  # Ensure to skip dynamically added kernel spec within the environment prefix
                # We're doing a few of these adjustments here to ensure that
                # the naming convention is as close as possible to the previous
                # versions of this package; particularly so that the tests
                # pass without change.
                if kernel_name in ('python2', 'python3'):
                    kernel_name = 'py'
                elif kernel_name == 'ir':
                    kernel_name = 'r'
                is_base = env_name == self.base_name
                kernel_prefix = '' if is_base else 'env-'
                kernel_name = u'conda-{}{}-{}'.format(kernel_prefix, env_name, kernel_name)
                # Replace invalid characters with dashes
                kernel_name = self.clean_kernel_name(kernel_name)

                display_prefix = spec['display_name']
                if display_prefix.startswith('Python'):
                    display_prefix = 'Python'
                display_name = self.name_format.format(
                    display_prefix,
                    env_name,
                    conda_kernel=kernel_name,
                    display_name=spec['display_name'],
                    environment=env_name,
                    kernel=raw_kernel_name,
                    language=display_prefix,
                )
                is_current = env_path == sys.prefix
                if is_current:
                    display_name += ' *'
                spec['display_name'] = display_name
                if env_path != sys.prefix:
                    spec['argv'] = RUNNER_COMMAND + [conda_prefix, env_path] + spec['argv']
                metadata = spec.get('metadata', {})
                metadata.update({
                    'conda_env_name': env_name,
                    'conda_env_path': env_path,
                    'conda_language': display_prefix,
                    'conda_raw_kernel_name': raw_kernel_name,
                    'conda_is_base_environment': is_base,
                    'conda_is_currently_running': is_current
                })
                if self.enable_debugger is not None:
                    metadata.update({"debugger": self.enable_debugger})
                spec['metadata'] = metadata

                if self.kernelspec_path is not None:
                    # Install the kernel spec
                    try:
                        destination = self.install_kernel_spec(
                            kernel_dir,
                            kernel_name=kernel_name,
                            user=self._kernel_user,
                            prefix=self._kernel_prefix
                        )
                        # Update the kernel spec
                        kernel_spec = join(destination, "kernel.json")
                        tmp_spec = spec.copy()
                        if env_path == sys.prefix:  # Add the conda runner to the installed kernel spec
                            tmp_spec['argv'] = RUNNER_COMMAND + [conda_prefix, env_path] + spec['argv']
                        with open(kernel_spec, "w") as f:
                            json.dump(tmp_spec, f)
                    except OSError as error:
                        self.log.warning(
                            u"nb_conda_kernels | Fail to install kernel '{}'.".format(kernel_dir),
                            exc_info=error
                        )

                # resource_dir is not part of the spec file, so it is added at the latest time
                spec['resource_dir'] = abspath(kernel_dir)

                all_specs[kernel_name] = spec

        # Remove non-existing conda environments
        if self.kernelspec_path is not None:
            kernels_destination = self._get_destination_dir(
                "",
                user=self._kernel_user,
                prefix=self._kernel_prefix
            )
            for folder in glob.glob(join(kernels_destination, "*", "kernel.json")):
                kernel_dir = dirname(folder)
                kernel_name = basename(kernel_dir)
                if kernel_name.startswith("conda-") and kernel_name not in all_specs:
                    self.log.info("Removing %s", kernel_dir)
                    if os.path.islink(kernel_dir):
                        os.remove(kernel_dir)
                    else:
                        shutil.rmtree(kernel_dir)

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

    def find_kernel_specs(self):
        """ Returns a dict mapping kernel names to resource directories.

            The update process also adds the resource dir for the conda
            environments.
        """
        if self.conda_only:
            kspecs = {}
        else:
            kspecs = super(CondaKernelSpecManager, self).find_kernel_specs()
            kspecs = {k: _canonicalize(v) for k, v in kspecs.items()}
        spec_rev = {v: k for k, v in kspecs.items()}
        for name, spec in self._conda_kspecs.items():
            kspecs[name] = spec.resource_dir
            dup = spec_rev.get(kspecs[name])
            if dup:
                del kspecs[dup]
        allow = getattr(self, 'allowed_kernelspecs', None) or getattr(self, 'whitelist', None)
        if allow:
            kspecs = {k: v for k, v in kspecs.items() if k in allow}
        return kspecs

    def get_kernel_spec(self, kernel_name):
        """ Returns a :class:`KernelSpec` instance for the given kernel_name.

            Additionally, conda kernelspecs are generated on the fly
            accordingly with the detected environments.
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

    def remove_kernel_spec(self, name):
        """Remove a kernel spec directory by name.

        Returns the path that was deleted.
        """
        save_native = self.ensure_native_kernel
        try:
            self.ensure_native_kernel = False
            # Conda environment kernelspec are only virtual, so remove can only be applied
            # on non-virtual kernels.
            specs = super(CondaKernelSpecManager, self).find_kernel_specs()
        finally:
            self.ensure_native_kernel = save_native
        spec_dir = specs[name]
        self.log.debug("Removing %s", spec_dir)
        if os.path.islink(spec_dir):
            os.remove(spec_dir)
        else:
            shutil.rmtree(spec_dir)
        return spec_dir

    def __del__(self):
      t = getattr(self, '_conda_info_cache_thread', None)
      # if there is a thread, wait for it to finish
      if t:
        t.join()

    def wait_for_child_processes_cleanup(self):
        p = psutil.Process()
        for c in p.children():
            try:
                c.wait(timeout=0)
            except psutil.TimeoutExpired:
                pass
