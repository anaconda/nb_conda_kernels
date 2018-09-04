import argparse
import json
import logging
import os
import sys

from os.path import exists, join, abspath

from traitlets.config.manager import BaseJSONConfigManager
from traitlets.config.loader import JSONFileConfigLoader, ConfigFileNotFound
from jupyter_core.paths import jupyter_config_dir, jupyter_config_path


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
ENDIS = ['disabled', 'enabled']


def pretty(it):
    return json.dumps(it, indent=2)


def get_status(path, warn_if_mismatch=True):
    all_paths = jupyter_config_path()
    try:
        cfg_all = JSONFileConfigLoader(JNC + '.json', path=all_paths).load_config()
    except ConfigFileNotFound:
        cfg_all = {}
    log.debug("Global configuration:\n{}".format(pretty(cfg_all)))
    is_enabled_all = cfg_all.get(NBA, {}).get(KSMC, None) == CKSM

    cfg = BaseJSONConfigManager(config_dir=path).get(JNC)
    log.debug("Local configuration ({}{}{}.json):\n{}".format(path, os.sep, JNC, pretty(cfg)))
    is_enabled_local = cfg.get(NBA, {}).get(KSMC, None) == CKSM

    if is_enabled_all != is_enabled_local and warn_if_mismatch:
        mode_g = ENDIS[is_enabled_all].upper()
        mode_l = ENDIS[is_enabled_local].upper()
        log.warn('''WARNING: The global setting is overriding local settings:
  Global setting: {}
  Local setting: {}
This can happen for several reasons:
  - The --prefix argument does not point to sys.prefix
  - The --path argument does not point to a directory
    searched by this installation of Jupyter
  - NotebookApp.kernel_spec_manager_class is set in
    another directory on the configuration path'''.format(mode_g, mode_l))
        if log.getEffectiveLevel() == logging.INFO:
            log.warn("Use the --verbose flag for more information.")

    return is_enabled_all, is_enabled_local


def install(enable=False, disable=False, status=None, prefix=None, path=None, verbose=False):
    """Installs the nb_conda_kernels configuration data.

    Parameters
    ----------
    enable: bool
    disable: bool
    status: bool
        Enable/disable nb_conda_kernels on every notebook launch,
        or simply check the status of installation, respectively.
        Exactly one of these should be supplied.
    prefix: None
    path: None
        The prefix of the Python environment where the Jupyter
        configuration is to be found and/or created, or the full
        path to jupyter_notebook_config.json, respecitvely. Exactly
        one of these should be supplied. If prefix is supplied, it
        is equivalent to path = join(prefix, 'etc', 'jupyter'). If
        neither is supplied, jupyter_core.paths.jupyter_config_path()
        will be searched for the first path within sys.prefix. If
        there are none, the first path will be selected.
    verbose: bool, default False
    """
    if verbose:
        log.setLevel(logging.DEBUG)
    if status:
        log.info("Determining the status of nb_conda_kernels...")
    else:
        log.info("{}ing nb_conda_kernels...".format(ENDIS[enable][:-2].capitalize()))

    all_paths = jupyter_config_path()
    if path or prefix:
        if prefix:
            path = join(prefix, "etc", "jupyter")
        if path not in all_paths:
            log.warn('WARNING: the prefix is not on the current jupyter config path')
        path = abspath(path)
    else:
        prefix_s = sys.prefix + os.sep
        for path in all_paths:
            if path.startswith(prefix_s):
                break
        else:
            log.warn('WARNING: no path within sys.prefix was found')
            path = all_paths[0]
    log.debug('Path: {}'.format(path))

    is_enabled_all, is_enabled_local = get_status(path, not disable)

    if status:
        log.info('Status: {}'.format(ENDIS[is_enabled_all]))
        return
    elif is_enabled_all == enable:
        log.info("Already {}, no change required".format(ENDIS[enable]))
        return
    elif is_enabled_local == enable:
        log.info("No change required to local configuration")
    else:
        cm = BaseJSONConfigManager(config_dir=path)
        cfg = cm.get(JNC)
        if enable:
            log.debug('Adding to local configuration')
            cfg.setdefault(NBA, {})[KSMC] = CKSM
        else:
            log.debug('Removing from local configuration')
            cfg[NBA].pop(KSMC)
            if not cfg[NBA]:
                cfg.pop(NBA)
        log.debug("Writing config in {}...".format(path))
        cm.set(JNC, cfg)

    is_enabled_all, is_enabled_local = get_status(path, True)
    if is_enabled_all != enable:
        raise RuntimeError('Could not {} nb_conda_kernels'.format(ENDIS[enable][:-1]))
    log.info("{} nb_conda_kernels".format(ENDIS[enable].capitalize()))


if __name__ == '__main__':
    install(**parser.parse_args().__dict__)
