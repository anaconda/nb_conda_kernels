# -*- coding: utf-8 -*-
import json
import subprocess
import sys

from os.path import exists, join, split, dirname, abspath

from jupyter_client.kernelspec import KernelSpecManager, KernelSpec, NATIVE_KERNEL_NAME


class CondaKernelSpecManager(KernelSpecManager):
    """A custom KernelSpecManager able to search for conda environments and
    create kernelspecs for them.
    """
    def __init__(self, **kwargs):
        super(CondaKernelSpecManager, self).__init__(**kwargs)
        self.conda_info = None
        specs = self.find_kernel_specs() or {}
        self.log.info("[nb_conda_kernels] enabled, {} kernels found".format(
            len(specs)
        ))
        self.log.debug("\n{}".format(
            "\n".join(["- {}: {}".format(*spec) for spec in specs.items()])
        ))

    def _conda_info(self):
        "Get and parse the whole conda information"
        p = subprocess.check_output(["conda", "info", "--json"]
                                    ).decode("utf-8")
        conda_info = json.loads(p)

        return conda_info

    def _all_envs(self):
        """Find the all the executables for each env where jupyter is installed.

        Returns a dict with the env names as keys and info about the kernel specs,
        including the paths to the lang executable in each env as value if jupyter
        is installed in that env.
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

        def get_paths_by_env(display_prefix, language_key, language_exe, envs):
            "Get a dict with name_env:info for kernel executables"
            language_envs = {}
            for base in envs:
                exe_path = join(base, language_exe)
                if exists(join(base, jupyter)) and exists(exe_path):
                    env_name = split(base)[1]
                    name = 'conda-env-{}-{}'.format(env_name, language_key)
                    language_envs[name] = {
                        'display_name': '{} [conda env:{}]'.format(
                            display_prefix, env_name),
                        'executable': exe_path,
                        'language_key': language_key,
                    }
            return language_envs

        # Collect all the envs in one dict
        all_envs = {}

        # Get the python envs
        python_envs = get_paths_by_env("Python", "py", python,
                                       self.conda_info["envs"])
        all_envs.update(python_envs)

        # Get the R envs
        r_envs = get_paths_by_env("R", "r", r, self.conda_info["envs"])
        all_envs.update(r_envs)

        # We also add the root prefix into the soup
        root_prefix = join(self.conda_info["root_prefix"], jupyter)
        if exists(root_prefix):
            all_envs.update({
                'conda-root-py': {
                    'display_name': 'Python [conda root]',
                    'executable': join(self.conda_info["root_prefix"], python),
                    'language_key': 'py',
                }
            })
        # Use Jupyter's default kernel name ('python2' or 'python3') for current env
        if exists(join(sys.prefix, jupyter)) and exists(join(sys.prefix, python)):
            all_envs.update({
                NATIVE_KERNEL_NAME: {
                    'display_name': 'Python [default]',
                    'executable': join(sys.prefix, python),
                    'language_key': 'py',
                }
            })

        return all_envs

    def _conda_kspecs(self):
        "Create a kernelspec for each of the envs where jupyter is installed"
        kspecs = {}
        for name, info in self._all_envs().items():
            executable = info['executable']
            display_name = info['display_name']

            if info['language_key'] == 'py':
                kspec = {
                    "argv": [executable, "-m", "ipykernel", "-f",
                             "{connection_file}"],
                    "display_name": display_name,
                    "language": "python",
                    "env": {},
                    "resource_dir": join(dirname(abspath(__file__)), "logos",
                                         "python")
                 }
            elif info['language_key'] == 'r':
                kspec = {
                    "argv": [executable, "--quiet", "-e", "IRkernel::main()",
                             "--args", "{connection_file}"],
                    "display_name": display_name,
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

        # update conda info
        self.conda_info = self._conda_info()

        # add conda envs kernelspecs
        kspecs.update(self._conda_kspecs())

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
