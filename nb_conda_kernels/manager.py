# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import re

from os.path import exists, join, split, dirname, abspath

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec


class CondaKernelSpecManager(KernelSpecManager):
    """A custom KernelSpecManager able to search for conda environments and
    create kernelspecs for them.
    """
    def __init__(self, **kwargs):
        super(CondaKernelSpecManager, self).__init__(**kwargs)
        self.conda_info = None
        self.log.info("[nb_conda_kernels] enabled, found:\n{}".format(
            "\n".join((self.find_kernel_specs() or {}).keys())
        ))

    def _conda_info(self):
        "Get and parse the whole conda information"
        p = subprocess.check_output(["conda", "info", "--json"]
                                    ).decode("utf-8")
        conda_info = json.loads(p)

        return conda_info

    def _all_executable(self):
        """Find the all the executables for each env where jupyter is installed.

        Returns a dict with the envs names as keys and the paths to the lang
        exectuable in each env as value if jupyter is installed in that env.
        """
        # play safe with windows
        if sys.platform.startswith('win'):
            python = join("python.exe")
            r = join("Scripts", "R.exe")
            jupyter = join("Scripts", "jupyter.exe")
        else:
            python = join("bin", "python")
            r = join("bin", "R")
            jupyter = join("bin", "jupyter")

        def get_paths_by_exe(prefix, language, envs):
            "Get a dict with name_env:path for agnostic executable"
            language_exe = {
                prefix + "[{}]".format(split(base)[1]): join(base, language)
                for base in envs
                if exists(join(base, jupyter)) and exists(join(base, language))
            }
            return language_exe

        # Collect all the executables in one dict
        all_exe = {}

        # Get the python executables
        python_exe = get_paths_by_exe("Python ", python,
                                      self.conda_info["envs"])
        all_exe.update(python_exe)

        # Get the R executables
        r_exe = get_paths_by_exe("R ", r, self.conda_info["envs"])
        all_exe.update(r_exe)

        # We also add the root prefix into the soup
        root_prefix = join(self.conda_info["root_prefix"], jupyter)
        if exists(root_prefix):
            all_exe.update({
                "Python [Root]": join(self.conda_info["root_prefix"], python)
            })

        return all_exe

    def _conda_kspecs(self):
        "Create a kernelspec for each of the envs where jupyter is installed"
        kspecs = {}
        for name, executable in self._all_executable().items():
            if re.search(r'python(\.exe)?$', executable):
                kspec = {
                    "argv": [executable, "-m", "ipykernel", "-f",
                             "{connection_file}"],
                    "display_name": name,
                    "language": "python",
                    "env": {},
                    "resource_dir": join(dirname(abspath(__file__)), "logos",
                                         "python")
                 }
            elif re.search(r'R(\.exe)?$', executable):
                kspec = {
                    "argv": [executable, "--quiet", "-e", "IRkernel::main()",
                             "--args", "{connection_file}"],
                    "display_name": name,
                    "language": "R",
                    "env": {},
                    "resource_dir": join(dirname(abspath(__file__)), "logos",
                                         "r")
                }

            kspecs.update({
                name: KernelSpec(**kspec)
            })

        return kspecs

    def find_kernel_specs(self):
        """Returns a dict mapping kernel names to resource directories.

        The update process also add the resource dir for the conda
        environments.
        """
        kspecs = super(CondaKernelSpecManager, self).find_kernel_specs()

        # remove native kernels because it is provided by the env name
        if "python3" in kspecs:
            kspecs.pop("python3")
        elif "python2" in kspecs:
            kspecs.pop("python2")
        elif "R" in kspecs:
            kspecs.pop("R")

        # update conda info
        self.conda_info = self._conda_info()

        # add conda envs kernelspecs
        kspecs.update(self._all_executable())

        return kspecs

    def get_kernel_spec(self, kernel_name):
        """Returns a :class:`KernelSpec` instance for the given kernel_name.

        Additionally, conda kernelspecs are generated on the fly accordingly
        with the detected envitonments.
        """
        conda_kspecs = self._conda_kspecs()
        if kernel_name in conda_kspecs:
            return conda_kspecs[kernel_name]
        else:
            return super(CondaKernelSpecManager, self).get_kernel_spec(
                kernel_name)
