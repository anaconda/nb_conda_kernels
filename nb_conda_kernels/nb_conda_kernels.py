# -*- coding: utf-8 -*-

import json
import subprocess
import sys

from os.path import exists, join, split

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec

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

    def _all_executable(self):
        """Find the all the executables for each env where jupyter is installed.

        Returns a dict with the envs names as keys and the paths to the lang
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
            r = join("Scripts", "R")
            jupyter = join("Scripts", "jupyter")
        else:
            python = join("bin", "python")
            r = join("bin", "R")
            jupyter = join("bin", "jupyter")

        def get_paths_by_exe(language, envs):
            "Get a dict with name_env:path for agnostic executable"
            language_exe = {split(base)[1]: join(base, language)
                            for base in envs if exists(join(base, jupyter))}
            return language_exe

        # Collect all the executables in one dict
        all_exe = {}

        # Get the python executables
        python_exe = get_paths_by_exe(python, conda_info["envs"])
        all_exe.update(python_exe)

        # Get the R executables
        r_exe = get_paths_by_exe(r, conda_info["envs"])
        all_exe.update(r_exe)

        # We also add the root prefix into the soup
        root_prefix = join(conda_info["root_prefix"], jupyter)
        if exists(root_prefix):
            all_exe.update({"root": join(conda_info["root_prefix"], python)})

        return all_exe

    def _conda_kspecs(self):
        "Create a kernelspec for each of the envs where jupyter is installed"
        kspecs = {}
        for name, executable in self._all_executable().items():
            if executable.endswith("python"):
                kspec =  {"argv": [executable, "-m", "ipykernel", "-f", "{connection_file}"],
                          "display_name": "Py-" + name,
                          "language": "python",
                          "env": {}}
            elif executable.endswith("R"):
                kspec =  {"argv": [executable, "--quiet", "-e","IRkernel::main()","--args","{connection_file}"],
                          "display_name": "R-" + name,
                          "language": "R",
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
        elif "R" in kspecs:
            kspecs.pop("R")

        # add conda envs kernelspecs
        kspecs.update(self._all_executablecutable())

        return kspecs

    def get_kernel_spec(self, kernel_name):
        """Returns a :class:`KernelSpec` instance for the given kernel_name.

        Additionally, conda kernelspecs are generated on the fly accordingly
        with the detected envitonments.
        """
        if kernel_name in self._conda_kspecs():
            return self._conda_kspecs()[kernel_name]
        else:
            return super(CondaKernelSpecManager, self).get_kernel_spec(kernel_name)
