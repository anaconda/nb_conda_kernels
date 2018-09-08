import argparse
import json
import logging
import os
import sys

from os.path import exists, join, abspath

from traitlets.config.manager import BaseJSONConfigManager
from jupyter_core.paths import jupyter_config_path

from .patch import status as patch_status, patch, VERSION
from .install import status as install_status, enable, disable


log = logging.getLogger('nb_conda_kernels')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


# Arguments for command line
parser = argparse.ArgumentParser(
    prog="python -m nb_conda_kernels",
    description="Manages the nb_conda_kernels notebook extension.")
parser.add_argument(
    "-v", "--verbose",
    help="show more output",
    action="store_true")
subparsers = parser.add_subparsers(dest='command')
subparsers.add_parser(
    "status",
    help="Print the status of the nb_conda_kernels installation.")
list_p = subparsers.add_parser(
    "list",
    help="List the kernels visible to nb_conda_kernels.")
list_p.add_argument(
    "--json",
    help="return JSON output",
    action="store_true")
subparsers.add_parser(
    "enable",
    help=("Modify the Jupyter Notebook configuration so that it uses "
          "nb_conda_kernels for kernel discovery. This is the original "
          "approach to enabling nb_conda_kernels, and works only with "
          "notebooks. To use nb_conda_kernels with the Jupyter console "
          "or nbconvert, use 'patch'."))
subparsers.add_parser(
    "patch",
    help=("Patch jupyter_client to use nb_conda_kernels. For notebooks, "
          "this provides the same functionality as 'enable', but this "
          "also enables it to work with other Jupyter applications."))
subparsers.add_parser(
    "disable",
    help=("Remove nb_conda_kernels from operation, by removing the "
          "configuration setting or the patch."))


def main(**kwargs):
    if kwargs.get('verbose'):
        log.setLevel(logging.DEBUG)
    verbose = log.getEffectiveLevel() == logging.DEBUG
    command = kwargs.get('command')

    if command == 'list':
        from jupyter_client import kernelspec
        from .manager import CondaKernelSpecManager
        kernelspec.KernelSpecManager = CondaKernelSpecManager
        from jupyter_client.kernelspecapp import ListKernelSpecs
        lk = ListKernelSpecs()
        lk.json_output = bool(kwargs.get('json'))
        lk.start()
        return 0

    p_status = patch_status()
    i_status = install_status()
    desired = None

    if command == 'enable':
        desired = 'NOTEBOOKS ONLY'
        log.info('Enabling nb_conda_kernels for notebooks...')
        if p_status:
            log.info('Already enabled by patch; no change made.')
            desired = 'ENABLED'
        elif i_status:
            log.info('Already enabled for notebooks; no change made.')
        else:
            enable()
            i_status = install_status()

    elif command == 'disable':
        desired = 'DISABLED'
        log.info('Disabling nb_conda_kernels...')
        if not i_status and not p_status:
            log.info('Already disabled; no change made.')
        if p_status:
            log.info('Removing jupyter_client patch...')
            patch(uninstall=True)
            p_status = patch_status()
        if i_status:
            log.info('Removing notebook configuration...')
            disable()
            i_status = install_status()

    elif command == 'patch':
        desired = 'ENABLED'
        log.info('Patching jupyter_client.kernelspec...')
        if p_status:
            log.info('Patch already applied; no change made.')
        else:
            patch()
            p_status = patch_status()

    mode_g = 'ENABLED' if p_status else ('NOTEBOOKS ONLY' if i_status else 'DISABLED')
    print('nb_conda_kernels status: {}'.format(mode_g))
    mode = 'ENABLED' if p_status else 'DISABLED'
    print('  - jupyter_client patch: {}'.format(mode))
    mode = 'ENABLED' if i_status else 'DISABLED'
    print('  - notebook configuration: {}'.format(mode))
    return desired is not None and mode_g != desired


main(**(parser.parse_args().__dict__))
