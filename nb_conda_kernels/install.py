#!/usr/bin/env python
# coding: utf-8

# Copyright (c) - Continuum Analytics

import argparse
import os
from os.path import exists, join
import json
import logging

from traitlets.config.manager import BaseJSONConfigManager

from jupyter_core.paths import (
    jupyter_config_dir,
    ENV_CONFIG_PATH,
    SYSTEM_CONFIG_PATH,
)


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

# Arguments for command line
parser = argparse.ArgumentParser(
    description="Installs nbextension")
parser.add_argument(
    "-e", "--enable",
    help="Automatically load nb_conda_kernels on notebook launch",
    action="store_true")
parser.add_argument(
    "-d", "--disable",
    help="Remove nb_conda_kernels from config on notebook launch",
    action="store_true")

parser.add_argument(
    "--user",
    help="use HOME/.jupyter to update nb_user_sessions config",
    action="store_true",
    default=False)
parser.add_argument(
    "--sys-prefix",
    help="use sys.prefix to update nb_user_sessions config",
    action="store_true",
    default=False)

parser.add_argument(
    "-v", "--verbose",
    help="Show more output",
    action="store_true"
)

CKSM = "nb_conda_kernels.CondaKernelSpecManager"
KSMC = "kernel_spec_manager_class"


class ArgumentConflict(ValueError):
    pass


def pretty(it): return json.dumps(it, indent=2)


def _get_config_dir(user=False, sys_prefix=False):
    """Get the location of config files for the current context
    Returns the string to the enviornment
    Parameters
    ----------
    user : bool [default: False]
        Get the user's .jupyter config directory
    sys_prefix : bool [default: False]
        Get sys.prefix, i.e. ~/.envs/my-env/etc/jupyter
    """
    user = False if sys_prefix else user
    if user and sys_prefix:
        raise ArgumentConflict("Cannot specify more than one of user or"
                               " sys_prefix")
    if user:
        nbext = jupyter_config_dir()
    elif sys_prefix:
        nbext = ENV_CONFIG_PATH[0]
    else:
        nbext = SYSTEM_CONFIG_PATH[0]
    return nbext


def install(enable=False, disable=False, user=False, sys_prefix=False,
            verbose=False):
    """Install the nb_conda_kernels config piece.

    Parameters
    ----------
    enable: bool
        Enable the nb_conda_kernels on every notebook launch
    disable: bool
        Disable nb_conda_kernels on every notebook launch
    """
    if verbose:
        log.setLevel(logging.DEBUG)

    if enable == disable:
        log.error("Please provide (one of) --enable or --disable")
        raise ValueError(enable, disable)

    log.info("{}abling nb_conda_kernels...".format("En" if enable else "Dis"))

    path = _get_config_dir(user, sys_prefix)

    if not exists(path):
        log.debug("Making directory {}...".format(path))
        os.makedirs(path)

    cm = BaseJSONConfigManager(config_dir=path)
    cfg = cm.get("jupyter_notebook_config")

    log.debug("Existing config in {}...\n{}".format(path, pretty(cfg)))

    nb_app = cfg.setdefault("NotebookApp", {})

    if enable:
        nb_app.update({KSMC: CKSM})
    elif disable and nb_app.get(KSMC, None) == CKSM:
        nb_app.pop(KSMC)

    log.debug("Writing config in {}...".format(path))

    cm.set("jupyter_notebook_config", cfg)

    cfg = cm.get("jupyter_notebook_config")

    log.debug("Verifying config in {}...\n{}".format(path, pretty(cfg)))

    if enable:
        assert cfg["NotebookApp"][KSMC] == CKSM
    else:
        assert KSMC not in cfg["NotebookApp"]

    log.info("{}abled nb_conda_kernels".format("En" if enable else "Dis"))


if __name__ == '__main__':
    install(**parser.parse_args().__dict__)
