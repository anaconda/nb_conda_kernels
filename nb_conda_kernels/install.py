#!/usr/bin/env python
# coding: utf-8

# Copyright (c) - Continuum Analytics

import argparse
import os
from os.path import exists, join
from pprint import pprint

from jupyter_core.paths import jupyter_config_dir

def install(enable=False, disable=False, prefix=None):
    """Install the nb_conda_kernels config piece.

    Parameters
    ----------
    enable: bool
        Enable the nb_conda_kernels on every notebook launch
    disable: bool
        Disable nb_conda_kernels on every notebook launch
    """
    from notebook.services.config import ConfigManager

    if enable:
        if prefix is not None:
            path = join(prefix, "etc", "jupyter")
            if not exists(path):
                print("Making directory", path)
                os.makedirs(path)
        else:
            path = jupyter_config_dir()

        cm = ConfigManager(config_dir=path)
        print("Enabling nb_conda_kernels in", cm.config_dir)
        cfg = cm.get("jupyter_notebook_config")
        print("Existing config...")
        pprint(cfg)

        notebook_app = (cfg.setdefault("NotebookApp", {}))
        if "kernel_spec_manager_class" not in notebook_app:
            cfg["NotebookApp"]["kernel_spec_manager_class"] = "nb_conda_kernels.CondaKernelSpecManager"

        cm.update("jupyter_notebook_config", cfg)
        print("New config...")
        pprint(cm.get("jupyter_notebook_config"))

    if disable:
        if prefix is not None:
            path = join(prefix, "etc", "jupyter")
        else:
            path = jupyter_config_dir()

        cm = ConfigManager(config_dir=path)
        print("Disabling nb_conda_kernels in", cm.config_dir)
        cfg = cm.get("jupyter_notebook_config")
        print("Existing config...")
        pprint(cfg)

        kernel_spec_manager = cfg["NotebookApp"]["kernel_spec_manager_class"]

        if "nb_conda_kernels.CondaKernelSpecManager" == kernel_spec_manager:
            cfg["NotebookApp"].pop("kernel_spec_manager_class")

        cm.set("jupyter_notebook_config", cfg)
        print("New config...")
        pprint(cm.get("jupyter_notebook_config"))

if __name__ == '__main__':

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

    install(**parser.parse_args().__dict__)
