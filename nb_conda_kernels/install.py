import argparse
import json
import logging
import os
import sys

from os.path import join, abspath, exists

from jupyter_core.paths import jupyter_config_path

try:
    from notebook import __version__ as nb_version
except ImportError:
    nb_version = '999'

try:
    from jupyter_server.config_manager import BaseJSONConfigManager
except ImportError:
    try:
        from notebook.config_manager import BaseJSONConfigManager
    except ImportError:
        raise ImportError("Must have notebook>=5.3 or jupyter_server installed")


# If true, we need to add a NotebokApp entry into jupyter_config.json.
# If false, we should avoid doing so, since notebook 7 and later have
# removed direct support for kernel spec managers in favor of relying
# on jupyter_server.
NEED_NOTEBOOK = int(nb_version.split('.', 1)[0]) < 7


log = logging.getLogger(__name__)


JA = "JupyterApp"
NBA = "NotebookApp"
SA = "ServerApp"
CKSM = "nb_conda_kernels.CondaKernelSpecManager"
JKSM = "jupyter_client.kernelspec.KernelSpecManager"
KSMC = "kernel_spec_manager_class"
JC = "jupyter_config"
JNC = "jupyter_notebook_config"
ENDIS = ['disabled', 'enabled']


def shorten(path, prefix=True):
    if prefix and path.startswith(sys.prefix + os.sep):
        var = '%CONDA_PREFIX%' if sys.platform.startswith('win') else '$CONDA_PREFIX'
        return var + path[len(sys.prefix):]
    home = os.path.expanduser('~')
    if path.startswith(home + os.sep):
        var = '%USERPROFILE%' if sys.platform.startswith('win') else '~'
        return var + path[len(home):]
    return path


def install(enable=False, disable=False, status=None, prefix=None, path=None, verbose=False):
    """Installs the nb_conda_kernels configuration data.

    Parameters
    ----------
    enable: bool
        Enable nb_conda_kernels; that is, make the changes to
        the Jupyter notebook configuration so that it will is
        available for Jupyter notebooks.
    disable: bool
        Disable nb_conda_kernels.
    status: bool
        Print the installation status, but make no changes.
    Exactly one of enable/disable/status must be supplied.

    verbose: bool
        If true, print more verbose output during operation.

    prefix: None
        The prefix of the Python environment where the Jupyter
        configuration is to be created and/or modified. It is
        equivalent to supplying
            path = join(prefix, 'etc', 'jupyter')
    path: None
        The directory where the Jupyter configuration file is
        to be created and/or modified. The name of the file is
        hardcoded to jupyter_notebook_config.json.
    Either prefix or path may be supplied, but not both. If
    neither is supplied, then the first path found in
        jupyter_core_paths.jupyter_config_path()
    whose directory is within sys.prefix will be selected. If
    there is no such path, the first path will be selected.
    """
    if verbose:
        log.setLevel(logging.DEBUG)
    verbose = log.getEffectiveLevel() == logging.DEBUG
    if status:
        log.info("Determining the status of nb_conda_kernels...")
    else:
        log.info("{}ing nb_conda_kernels...".format(ENDIS[enable][:-2].capitalize()))
    log.info("CONDA_PREFIX: {}".format(sys.prefix))

    all_paths = [abspath(p) for p in jupyter_config_path()]
    default_path = join(sys.prefix, 'etc', 'jupyter')
    search_paths = all_paths[::-1]
    if path or prefix:
        if prefix:
            path = join(prefix, 'etc', 'jupyter')
        path = abspath(path)
    else:
        prefix_s = sys.prefix + os.sep
        for path in search_paths:
            if path.startswith(prefix_s):
                break
        else:
            path = default_path
    if path != default_path or path not in all_paths:
        log.info("Target path: {}".format(path))
    if path not in all_paths:
        log.warning('WARNING: the configuration for the current environment\n'
                    'is not affected by the target configuration path.')
        search_paths.append(path)

    # Determine the effective configuration by going through the search path
    # in reverse order. Moving forward we will be modifying only the JupyterApp
    # key in the jupyter_config.json file. However for legacy reasons we are
    # also looking at NotebookApp keys and the jupyter_notebook_config.json file,
    # and cleaning those out as we can.
    log.debug('Configuration files:')
    fpaths = set()
    is_enabled_all = {}
    is_enabled_local = {}
    need_keys = (SA, NBA) if NEED_NOTEBOOK else (SA,)
    for path_g in search_paths:
        flag = '-' if path != path_g else ('*' if path in all_paths else 'x')
        value = ''
        for fbase in (JC, JNC):
            fpath = join(path_g, fbase + '.json')
            cfg = BaseJSONConfigManager(config_dir=path_g).get(fbase)
            dirty = False
            for key in (JA, NBA, SA):
                spec = cfg.get(key, {}).get(KSMC)
                if status or path_g != path:
                    # No changes in status mode, or if we're not in the target path
                    expected = spec
                elif enable and fbase == JC and key in need_keys:
                    # Add the spec if we are enabling, the entry point is not active,
                    # and we're using the new file (jupyter_config.json) and key (JupyterApp)
                    expected = CKSM
                else:
                    # In all other cases, clear the spec out for cleanup
                    expected = None
                if spec != expected:
                    if expected is None:
                        cfg[key].pop(KSMC)
                        if not cfg[key]:
                            cfg.pop(key)
                    else:
                        cfg.setdefault(key, {})[KSMC] = expected
                    spec = expected
                    dirty = True
                if spec:
                    if path_g in all_paths:
                        is_enabled_all[key] = spec == CKSM
                    if path_g == path:
                        is_enabled_local[key] = spec == CKSM
                    else:
                        fpaths.add(join(path_g, fbase + '.json'))
            if dirty:
                BaseJSONConfigManager(config_dir=path).set(fbase, cfg)
            if dirty or exists(fpath):
                value += '\n      ' + fbase + '.json'
                if dirty:
                    value += ' (MODIFIED)'
                value += ': '
                value += '\n        '.join(json.dumps(cfg, indent=2).splitlines())
        log.debug('  {} {}: {}'.format(flag, shorten(path_g), value or '<no files>'))
    is_enabled_all = all(is_enabled_all.get(k) for k in need_keys)
    is_enabled_local = all(is_enabled_local.get(k) for k in need_keys)

    if is_enabled_all != is_enabled_local:
        sev = 'WARNING' if status else 'ERROR'
        if path not in all_paths:
            msg = fpaths = []
        elif status:
            msg = ['{}: the local configuration of nb_conda_kernels'.format(sev),
                   'conflicts with the global configuration. Please examine']
        else:
            what = ENDIS[is_enabled_local][:-1]
            msg = ['{}: the attempt to {} nb_conda_kernels failed due to'.format(sev, what),
                   'conflicts with global configuration files. Please examine']
        if fpaths:
            msg.append('the following file{} for potential conflicts:'
                       .format('s' if len(fpaths) > 1 else ''))
            for fpath in fpaths:
                msg.append('    ' + shorten(fpath, False))
            if not verbose:
                msg.append('Use the --verbose flag for more information.')
        if msg:
            (log.warning if status else log.error)('\n'.join(msg))

    log.info('Status: {}'.format(ENDIS[is_enabled_all]))
    return 0 if status or is_enabled_all == is_enabled_local else 1


if __name__ == '__main__':
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.INFO)

    # Arguments for command line
    parser = argparse.ArgumentParser(
        description="Installs the nb_conda_kernels notebook extension")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-s", "--status",
        help="Print the current status of nb_conda_kernels installation",
        action="store_true")
    group.add_argument(
        "-e", "--enable",
        help="Automatically load nb_conda_kernels on notebook launch",
        action="store_true")
    group.add_argument(
        "-d", "--disable",
        help="Remove nb_conda_kernels from config on notebook launch",
        action="store_true")
    group2 = parser.add_mutually_exclusive_group(required=False)
    group2.add_argument(
        "-p", "--prefix",
        help="Prefix where to load nb_conda_kernels config (default: sys.prefix)",
        action="store")
    group2.add_argument(
        "--path",
        help="Absolute path to the jupyter configuration directory",
        action="store")
    parser.add_argument(
        "-v", "--verbose",
        help="Show more output",
        action="store_true"
    )

    exit(install(**parser.parse_args().__dict__))
