import argparse
import json
import logging
import os
import sys

from os.path import join, abspath, exists
from pkg_resources import iter_entry_points

from traitlets.config.manager import BaseJSONConfigManager
from jupyter_core.paths import jupyter_config_path
from jupyter_client import __version__ as jc_version


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
JCKP = "jupyter_client.kernel_providers"
NCKDCKP = "nb_conda_kernels.discovery:CondaKernelProvider"
ENDIS = ['disabled', 'enabled']


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

    is_enabled_entry = False
    # Disable the entry-point based mechanism. Most if this code will need
    # to be removed, because the kernel discovery mechanism was changed
    # before jupyter_client 6 was released. For now we're dropping back to
    # the jupyter_client 5 model until we leverage the new mechanism.
    has_entrypoints = False # int(jc_version.split('.', 1)[0]) >= 6
    log.debug('Entry points:')
    for ep in iter_entry_points(group=JCKP):
        log.debug('  - {}'.format(ep))
        if str(ep).split('=', 1)[-1].strip() == NCKDCKP:
            is_enabled_entry = True
    if not is_enabled_entry and has_entrypoints:
        log.error(('NOTE: nb_conda_kernels is missing its entry point '
                   'for jupyter_client.kernel_providers, which is needed '
                   'for correct operation with Jupyter 6.0.'))
    if is_enabled_entry and not has_entrypoints:
        log.debug('  NOTE: entry points not used in Jupyter {}'.format(jc_version))
        is_enabled_entry = False

    all_paths = jupyter_config_path()
    if path or prefix:
        if prefix:
            path = join(prefix, 'etc', 'jupyter')
        if path not in all_paths:
            log.warn('WARNING: the requested path\n    {}\n'
                     'is not on the Jupyter config path'.format(path))
    else:
        prefix_s = sys.prefix + os.sep
        for path in all_paths[::-1]:
            if path.startswith(prefix_s):
                break
        else:
            log.warn('WARNING: no path within sys.prefix was found')

    cfg = BaseJSONConfigManager(config_dir=path).get(JNC)
    is_enabled_local = cfg.get(NBA, {}).get(KSMC, None) == CKSM

    if not status and is_enabled_local != (enable and not is_enabled_entry):
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
    log.debug('{} entries:'.format(JNCJ))
    is_enabled_all = False
    search_paths = all_paths[::-1]
    if path not in all_paths:
        search_paths.append(path)
    for path_g in search_paths:
        cfg_g = BaseJSONConfigManager(config_dir=path_g).get(JNC)
        flag = '-' if path != path_g else ('*' if path in all_paths else 'x')
        if exists(join(path_g, JNCJ)):
            value =  '\n    '.join(json.dumps(cfg_g, indent=2).splitlines())
            if NBA in cfg_g and KSMC in cfg_g[NBA]:
                is_enabled_all = cfg_g[NBA][KSMC] == CKSM
        else:
            value = '<no file>'
        log.debug('  {} {}: {}'.format(flag, path_g, value))

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

    is_enabled_all = is_enabled_all or (has_entrypoints and is_enabled_entry)
    log.info('Status: {}'.format(ENDIS[is_enabled_all]))
    return 0


if __name__ == '__main__':
    exit(install(**parser.parse_args().__dict__))
