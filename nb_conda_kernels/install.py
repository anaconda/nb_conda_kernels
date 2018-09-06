import argparse
import json
import logging
import os
import sys

from os.path import exists, join, abspath

from traitlets.config.manager import BaseJSONConfigManager
from jupyter_core.paths import jupyter_config_path


log = logging.getLogger(__name__)
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
    help="Absolute path to jupyter_notebook_config.json",
    action="store")
parser.add_argument(
    "-v", "--verbose",
    help="Show more output",
    action="store_true"
)


NBA = "NotebookApp"
CKSM = "nb_conda_kernels.CondaKernelSpecManager"
KSMC = "kernel_spec_manager_class"
JNC = "jupyter_notebook_config"
JNCJ = JNC + ".json"
ENDIS = ['disabled', 'enabled']


def pretty(it):
    return json.dumps(it, indent=2)


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

    all_paths = jupyter_config_path()
    if path or prefix:
        if prefix:
        	path = join(prefix, 'etc', 'jupyter')
        if path not in all_paths:
            log.warn('WARNING: the requested path\n    {}\n'
                     'is not on the Jupyter config path'.format(path))
    else:
        prefix_s = sys.prefix + os.sep
        for path in all_paths:
            if path.startswith(prefix_s):
                break
        else:
            log.warn('WARNING: no path within sys.prefix was found')
            path = all_paths[0]
    path = abspath(path)
    log.debug('Path: {}'.format(path))

    cfg = BaseJSONConfigManager(config_dir=path).get(JNC)
    log.debug("Local configuration ({}):\n{}".format(join(path, JNCJ), pretty(cfg)))
    is_enabled_local = cfg.get(NBA, {}).get(KSMC, None) == CKSM

    if not status and is_enabled_local != enable:
        if enable:
            log.debug('Adding to local configuration')
            cfg.setdefault(NBA, {})[KSMC] = CKSM
        else:
            log.debug('Removing from local configuration')
            cfg[NBA].pop(KSMC)
            if not cfg[NBA]:
                cfg.pop(NBA)
        log.debug("Writing config in {}...".format(path))
        BaseJSONConfigManager(config_dir=path).set(JNC, cfg)
        is_enabled_local = enable

    # Retrieve the global configuration the same way that the Notebook
    # app does: by looking through jupyter_notebook_config.json in
    # every directory in jupyter_config_path(), in reverse order.
    all_paths = jupyter_config_path()
    log.debug('Searching configuration path:')
    is_enabled_all = False
    for path_g in all_paths[::-1]:
        cfg_g = BaseJSONConfigManager(config_dir=path_g).get(JNC)
        if not cfg_g:
        	value = 'no data'
        elif NBA not in cfg_g:
        	value = 'no {} entry'.format(NBA)
        elif KSMC not in cfg_g[NBA]:
        	value = 'no {}.{} entry'.format(NBA, KSMC)
        else:
        	value = cfg_g[NBA][KSMC]
        	is_enabled_all = value == CKSM
        	value = '\n        {}: {}'.format(KSMC, value)
        log.debug('  - {}: {}'.format(path_g, value))

    if is_enabled_all != is_enabled_local:
        logsev = log.warn if status else log.error
        logstr = 'WARNING' if status else 'ERROR'
        mode_g = ENDIS[is_enabled_all].upper()
        mode_l = ENDIS[is_enabled_local].upper()
        logsev(('{}: The global setting does not match the local setting:\n'
                '    Global: {}\n'
                '    Local:  {}\n'
                'This is typically caused by another configuration file in\n'
                'the path with a conflicting setting.').format(logstr, mode_g, mode_l))
        if not verbose:
            logsev("Use the --verbose flag for more information.")
        if not status:
            return 1

    log.info('Status: {}'.format(ENDIS[is_enabled_all]))
    return 0


if __name__ == '__main__':
    exit(install(**parser.parse_args().__dict__))
