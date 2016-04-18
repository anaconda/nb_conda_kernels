#!/usr/bin/env python
# coding: utf-8

# Copyright (c) - Continuum Analytics

import argparse
import os
from os.path import exists, join
from pprint import pformat
import logging

from traitlets.config.manager import BaseJSONConfigManager

from jupyter_core.paths import jupyter_config_dir


log = logging.getLogger(__name__)

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
    "-p", "--prefix",
    help="prefix where to load nb_conda_kernels config",
    action="store")


def install(enable=False, disable=False, prefix=None):
    """Install the nb_conda_kernels config piece.

    Parameters
    ----------
    enable: bool
        Enable the nb_conda_kernels on every notebook launch
    disable: bool
        Disable nb_conda_kernels on every notebook launch
    """
    if not (enable or disable):
        raise Exception("Please provide --enable or --disable")

    if prefix is not None:
        path = join(prefix, "etc", "jupyter")
        if not exists(path):
            print("Making directory", path)
            os.makedirs(path)
    else:
        path = jupyter_config_dir()

    cm = BaseJSONConfigManager(config_dir=path)

    if enable:
        log.info("Enabling nb_conda_kernels in {}".format(cm.config_dir))
        cfg = cm.get("jupyter_notebook_config")
        log.info("Existing config...\n{}".format(
                 pformat(cfg)))

        notebook_app = (cfg.setdefault("NotebookApp", {}))
        if "kernel_spec_manager_class" not in notebook_app:
            cfg["NotebookApp"].set(
                "kernel_spec_manager_class",
                "nb_conda_kernels.CondaKernelSpecManager")

        cm.update("jupyter_notebook_config", cfg)
        log.info("New config...\n {}".format(
              pformat(cm.get("jupyter_notebook_config"))))
    elif disable:
        log.info("Disabling nb_conda_kernels in {}".format(cm.config_dir))
        cfg = cm.get("jupyter_notebook_config")
        log.info("Existing config...\n{}".format(pformat(cfg)))
        kernel_spec_manager = cfg["NotebookApp"]["kernel_spec_manager_class"]

        if "nb_conda_kernels.CondaKernelSpecManager" == kernel_spec_manager:
            cfg["NotebookApp"].pop("kernel_spec_manager_class")

        cm.set("jupyter_notebook_config", cfg)
        log.info("New config...\n{}".format(
                 pformat(cm.get("jupyter_notebook_config"))))


if __name__ == '__main__':
    install(**parser.parse_args().__dict__)
