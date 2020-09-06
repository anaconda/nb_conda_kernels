| [![Build and test the package](https://github.com/Anaconda-Platform/nb_conda_kernels/workflows/Build%20and%20test%20the%20package/badge.svg)](https://github.com/Anaconda-Platform/nb_conda_kernels/actions?query=workflow%3A%22Build+and+test+the+package%22) | [![Anaconda-Server Badge](https://anaconda.org/jupycon/nb_conda_kernels/badges/latest_release_date.svg)](https://anaconda.org/jupycon/nb_conda_kernels) |
| --- | :-: |
| [`conda install jupycon/label/dev::nb_conda_kernels`](https://anaconda.org/jupycon/nb_conda_kernels) | [![Anaconda-Server Badge](https://anaconda.org/jupycon/nb_conda_kernels/badges/version.svg)](https://anaconda.org/jupycon/nb_conda_kernels) |
| [`conda install defaults::nb_conda_kernels`](https://anaconda.org/anaconda/nb_conda_kernels) | [![Anaconda-Server Badge](https://anaconda.org/anaconda/nb_conda_kernels/badges/version.svg)](https://anaconda.org/anaconda/nb_conda_kernels) |
| [`conda install conda-forge::nb_conda_kernels`](https://anaconda.org/conda-forge/nb_conda_kernels) | [![Anaconda-Server Badge](https://anaconda.org/conda-forge/nb_conda_kernels/badges/version.svg)](https://anaconda.org/conda-forge/nb_conda_kernels) |

# nb_conda_kernels

This extension enables a [Jupyter Notebook](http://jupyter.org)
or [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/)
application in one [conda](https://conda.io/docs/)
environment to access kernels for Python, R, and other languages
found in other environments. When a kernel from an external environment is selected, the kernel conda environment is
automatically activated before the kernel is launched.
This allows you to utilize different versions of Python, R,
and other languages from a single Jupyter installation.

The package works by defining a custom `KernelSpecManager` that
scans the current set of `conda` environments for kernel
specifications. It dynamically modifies each `KernelSpec`
so that it can be properly run from the notebook environment.
When you create a new notebook, these modified kernels
will be made available in the selection list.

## Installation

This package is designed to be managed solely using `conda`.
It should be installed in the environment from which
you run Jupyter Notebook or JupyterLab. This might be your base
`conda` environment, but it need not be. For instance,
if the environment `notebook_env` contains the `notebook`
package, then you would run

```shell
conda install -n notebook_env nb_conda_kernels
```

Any _other_ environments you wish to access in your
notebooks must have an appropriate kernel
package installed. For instance, to access a Python
environment, it must have the `ipykernel` package; e.g.

```shell
conda install -n python_env ipykernel
```

To utilize an R environment, it must have the `r-irkernel` package; e.g.

```shell
conda install -n r_env r-irkernel
```

For other languages, their [corresponding kernels](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels)
must be installed.

### Use with nbconvert, voila, papermill,...

This extension works out of the box _only_ with Jupyter notebooks and
JupyterLab.

A new [kernel discovery system](https://github.com/jupyter/jupyter_server/pull/112)
is being developed that should enable the 
wider Jupyter ecosystem to take advantage of these external
kernels. This package will require modification to
function properly in this new system.

But you can activate a workaround for it to work with 
Jupyter Console, `nbconvert`, and other tools. As
these tools were not designed to allow for the use of custom
KernelSpecs, you can set the configuration parameter `kernelspec_path`
to tell this extension to add dynamically the conda environment to
the kernel list. To set it up:

1. Create a configuration file for jupyter named `jupyter_config.json`
in the folder returned by `jupyter --config-dir`.
2. Add the following configuration to install all kernel spec for the current user:
```json
{
  "CondaKernelSpecManager": {
    "kernelspec_path": "--user"
  }
}
```
3. Execute the command (or open the classical Notebook or JupyterLab UI):
```sh
python -m nb_conda_kernels list
```
4. Check that the conda environment kernels are discovered by `jupyter`:
```sh
jupyter kernelspec list
```
The previous command should list the same kernel than `nb_conda_kernels`.

You are now all set. `nbconvert`, `voila`, `papermill`,... should find the 
conda environment kernels.

## Configuration

This package introduces two additional configuration options:

- `conda_only`: Whether to include only the kernels not visible from Jupyter normally or not (default: False except if `kernelspec_path` is set)
- `env_filter`: Regex to filter environment path matching it. Default: `None` (i.e. no filter)
- `kernelspec_path`: Path to install conda kernel specs to if not `None`. Default: `None` (i.e. don't install the conda environment as kernel specs for other Jupyter tools)  
Possible values are:
  - `""` (empty string): Install for all users
  - `--user`: Install for the current user instead of system-wide
  - `--sys-prefix`: Install to Python's sys.prefix
  - `PREFIX`: Specify an install prefix for the kernelspec. The kernel specs will be
  written in `PREFIX/share/jupyter/kernels`. Be careful that the PREFIX
  may not be discoverable by Jupyter; set JUPYTER_DATA_DIR to force it or run 
  `jupyter --paths` to get the list of data directories.

- `name_format`: String name format; `'{0}'` = Language, `'{1}'` = Kernel. Default: `'{0} [conda env:{1}]'`

In order to pass a configuration option in the command line use ```python -m nb_conda_kernels list --CondaKernelSpecManager.env_filter="regex"``` where regex is the regular expression for filtering envs "this|that|and|that" works.
To set it in jupyter config file, edit the jupyter configuration file (py or json) located in your ```jupyter --config-dir```
- for `jupyter_config.py` - add a line "c.CondaKernelSpecManager.env_filter = 'regex'"
- for `jupyter_config.json` - add a json key 

```json
{
  "CondaKernelSpecManager": {
    "env_filter": "regex"
}
```

## Development

1. Install [Anaconda](https://www.anaconda.com/download/) or
   [Miniconda](https://conda.io/miniconda.html). If you are
   on Windows, make sure you have a Bash shell on your path.

2. Create and activate the testbed environment by running

   ```shell
   source testbed/build.sh
   ```

   This performs the following steps:
   - Builds a new root conda environment in `../nbckdev`,
     or in `CONDA_ROOT` if that environment variable is defined.
     (Note that the default directory `../nbckdev` is at the same
     level as your copy of the repository. This is because we do
     not want `conda build` to try to capture the entire testbed
     into the build workspace.)
   - Installs conda-build and the necessary dependencies to
     locally test the package
   - Installs the package in development mode
   - Creates a set of environments that the test scripts
     require to fully exercise the package.
   - Activates the environment, including a deliberate scrubbing
     of variables and paths from your primary conda environment.

   If the environment already exists, `testbed/build.sh` will
   quickly exit, so it is safe to run it if you are not sure.

3. Run pytest to test the package.

   ```shell
   pytest tests
   ```

4. The root environment of our testbed uses Python 3.7. If you would
   like to test `nb_conda_kernels` with a different Python version,
   create a new child environment:

   ```shell
   conda create -n ptest python=... notebook pytest pytest-cov requests mock
   conda install backports.functools_lru_cache # python 2 only
   conda activate ptest
   pip install -e .
   python -m nb_conda_kernels.install --enable
   pytest tests
   ```

## Changelog

### 2.3.0

- Provide a mechanism for using `nb_conda_kernels`
  with tools such as `voila`, `papermill`, `nbconvert`
- Preserve kernel metadata properly
- Testbed improvements

### 2.2.4

- Tested support for noarch packages
- Windows bug fixes
- Better documentation for `env_filter`
- Fixes to kernel metadata

### 2.2.3

- Restore compatibiltiy with Jupyter V6
- Testing and support for Python 3.8
- Enhanced kernelSpec metadata

### 2.2.2

- Adds project name to kernel name for environments that
  live outside of the default environment location
- Improved runner scripts: linear execution, better handling
  of environment variables
- Migrate from nosetests to pytest

### 2.2.1

- Put the default environment back into the conda-env list;
  the redundancy is worth the elimination of confusion.
- Fix post-link scripts on windows

### 2.2.0

- Perform full activation of kernel conda environments
- Discover kernels from their kernel specs, enabling the use
  of kernels besides Python and R
- Support for spaces and accented characters in environment
  paths, with properly validating kernel names
- Configurable format for kernel display names
- Remove NodeJS-based testing

### 2.1.1

- move to a full conda-based approach to build and test
- add support for conda 4.4 and later, which can remove `conda` from the PATH

### 2.1.0

- add support for regex-based filtering of conda environments that should not appear in the list

### 2.0.0

- change kernel naming scheme to leave default kernels in place

### 1.0.3

- ignore build cleanup on windows due to poorly-behaved PhantomJS processes

### 1.0.2

- use [Travis-CI](https://travis-ci.org/Anaconda-Platform/nb_conda_kernels) for continuous integration
- use [Coveralls](https://coveralls.io/github/Anaconda-Platform/nb_conda_kernels) for code coverage
- use a [conda-forge](https://github.com/conda-forge/nb_conda_kernels-feedstock) for cross-platform `conda` package building

### 1.0.1

- minor build changes

### 1.0.0

- update to notebook 4.2
