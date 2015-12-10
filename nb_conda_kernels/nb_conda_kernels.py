# -*- coding: utf-8 -*-

import json
import subprocess
import sys

from os.path import exists, join, split

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec, NoSuchKernel

class CondaKernelSpecManager(KernelSpecManager):
    """A custom KernelSpecManager able to search for conda environments and
    create kernelspecs for them.
    """
    # at /tree all the kernelspec are loaded... we need to get conda_info at
    # the very beginning to avoid a large loading time
    first_read = True

    def __init__(self, **kwargs):
        super(CondaKernelSpecManager, self).__init__(**kwargs)
        self.conda_info = self._conda_info()

    def _conda_info(self):
        "Get and parse the whole conda information"
        p = subprocess.check_output(["conda", "info", "--json"]).decode("utf-8")
        conda_info = json.loads(p)

        return conda_info

    def _python_executable(self):
        """Find the python executable for each env where jupyter is installed.

        Returns a dict with the envs names as keys and the paths to the python
        exectuable in each env as value if jupyter is installed in that env.
        """
        # First time we load the conda info from the __init__
        if self.first_read:
            conda_info = self.conda_info
            first_read = False
        # but after that, we check if there is not a new env
        else:
            update_conda_info = self._conda_info()
            if update_conda_info["envs"] == self.conda_info["envs"]:
                conda_info = self.conda_info
            else:
                conda_info = update_conda_info

        # play safe with windows
        if sys.platform.startswith('win'):
            python = join("Scripts", "python")
            jupyter = join("Scripts", "jupyter")
        else:
            python = join("bin", "python")
            jupyter = join("bin", "jupyter")

        # python_exe = {name_env: python_path_env}
        python_exe = {split(base)[1]: join(base, python)
                      for base in conda_info["envs"]
                      if exists(join(base, jupyter))}

        # We also add the root prefix into the soup
        root_prefix = join(conda_info["root_prefix"], jupyter)
        if exists(root_prefix):
            python_exe.update({"root": join(conda_info["root_prefix"], python)})

        return python_exe

    def _conda_kspecs(self):
        "Create a kernelspec for each of the envs where jupyter is installed"
        kspecs = {}
        for name, executable in self._python_executable().items():
            kspec =  {"argv": [executable, "-m", "ipykernel", "-f", "{connection_file}"],
                      "display_name": name,
                      "env": {}}
            kspecs.update({name: KernelSpec(**kspec)})

        return kspecs

    def find_kernel_specs(self):
        """Returns a dict mapping kernel names to resource directories.

        The update process also add the resource dir for the conda environments.
        """
        kspecs = super(CondaKernelSpecManager, self).find_kernel_specs()

        # remove native kernels because it is provided by the env name
        if "python3" in kspecs:
            kspecs.pop("python3")
        elif "python2" in kspecs:
            kspecs.pop("python2")

        # add conda envs kernelspecs
        kspecs.update(self._python_executable())

        return kspecs

    def get_kernel_spec(self, kernel_name):
        """Returns a :class:`KernelSpec` instance for the given kernel_name.

        Additionally, conda kernelspecs are generated on the fly accordingly
        with the detected envitonments.
        Raises :exc:`NoSuchKernel` if the given kernel name is not found.
        """
        if kernel_name in self._conda_kspecs():
            return self._conda_kspecs()[kernel_name]
        else:
            return super(CondaKernelSpecManager, self).get_kernel_spec(kernel_name)
