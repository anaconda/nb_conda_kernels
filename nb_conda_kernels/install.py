import logging
import os
import sys

from os.path import abspath

from traitlets.config.manager import BaseJSONConfigManager
from jupyter_core.paths import jupyter_config_path


log = logging.getLogger('nb_conda_kernels')


NBA = "NotebookApp"
CKSM = "nb_conda_kernels.manager.CondaKernelSpecManager"
KSMC = "kernel_spec_manager_class"
JNC = "jupyter_notebook_config"
JNCJ = JNC + ".json"
JCKP = "jupyter_client.kernel_providers"
NCKDCKP = "nb_conda_kernels.discovery:CondaKernelProvider"
ENDIS = ['disabled', 'enabled']

# Reverse the list so we the highest priority paths are last
ALL_PATHS = jupyter_config_path()[::-1]


def default_path():
    """Returns the directory where additions or modifications to
       jupyter_notebook_config.json will be made---the last (and,
       likely, only) directory within jupyter_config_path() that
       is a subdirectory of sys.prefix. Such a directory must
       exist, or an error will be thrown."""
    prefix_s = sys.prefix + os.sep
    for path in ALL_PATHS:
        if path.startswith(prefix_s):
            return path
    raise RuntimeError('Unexpected error: no configuration directory')


def status(path=None):
    """Returns True if the jupyter_notebook_config files enable
       the use of nb_conda_kernels, and False otherwise. Uses the
       standard Jupyter configuration dictionary merging convention
       to determine the global setting. A warning will be issued if
       the local setting, found in default_path(), is overridden by
       a higher-priority configuration file."""
    log.debug("Examining {}.json files:".format(JNC))
    is_enabled = is_enabled_local = False
    if path is None:
        path = default_path()
    for path_g in ALL_PATHS:
        cfg = BaseJSONConfigManager(config_dir=path_g).get(JNC)
        if not cfg:
            value = 'no data'
        elif NBA not in cfg:
            value = 'no {} entry'.format(NBA)
        elif KSMC not in cfg[NBA]:
            value = 'no {}.{} entry'.format(NBA, KSMC)
        else:
            value = cfg[NBA][KSMC]
            is_enabled = value == CKSM
            if path_g == path:
                is_enabled_local = is_enabled
            value = '\n        {}: {}'.format(KSMC, value)
        flag = ' (local)' if path_g == path else ''
        log.debug('    {}{}: {}'.format(path_g, flag, value))
    log.debug('    Final determination: {}'.format(ENDIS[is_enabled].upper()))

    if is_enabled != is_enabled_local:
        mode_g = ENDIS[is_enabled].upper()
        mode_l = ENDIS[is_enabled_local].upper()
        log.warn(('WARNING: The global setting does not match the local setting.\n'
                  'This is typically caused by another configuration file in\n'
                  'the path with a conflicting setting.').format(mode_g, mode_l))
        if log.getEffectiveLevel() != logging.DEBUG:
            log.warn("Use the -v/--verbose flag for more information.")

    return is_enabled


def enable(path=None):
    """Ensures that the KernelSpecManagerClass configuration
       is set to nb_conda_kernels.CondaKernelSpecManager in the
       jupyter_notebook_config.json file found in the directory
       given by the path parameter. If path is not supplied, it
       defaults to default_path(). If the setting is already
       correct, the file is not modified."""
    if path is None:
        path = default_path()
    log.debug('Path: {}'.format(path))
    cfg = BaseJSONConfigManager(config_dir=path).get(JNC)
    if cfg.get(NBA, {}).get(KSMC, None) == CKSM:
        log.debug('The setting is already present; no change needed.')
        return
    cfg.setdefault(NBA, {})[KSMC] = CKSM
    log.debug("Writing config in {}...".format(path))
    BaseJSONConfigManager(config_dir=path).set(JNC, cfg)


def disable(path=None):
    """Ensures that the KernelSpecManagerClass configuration
       is not equal to nb_conda_kernels.CondaKernelSpecManager
       in the jupyter_notebook_config.json file found in the
       directory given by the path parameter. If path is not
       supplied, it defaults to default_path(). If the setting
       is not present or not equal to this target value, the
       file is not modified."""
    if path is None:
        path = default_path()
    path = abspath(path)
    log.debug('Path: {}'.format(path))
    cfg = BaseJSONConfigManager(config_dir=path).get(JNC)
    if cfg.get(NBA, {}).get(KSMC, None) != CKSM:
        log.debug('The setting is not present; no change needed.')
        return
    log.debug('Removing from local configuration')
    cfg[NBA].pop(KSMC)
    if not cfg[NBA]:
        cfg.pop(NBA)
    log.debug("Writing config in {}...".format(path))
    BaseJSONConfigManager(config_dir=path).set(JNC, cfg)
