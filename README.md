| [![Travis Status](https://travis-ci.org/Anaconda-Platform/nb_conda_kernels.svg?branch=master)](https://travis-ci.org/Anaconda-Platform/nb_conda_kernels)&nbsp;[![AppVeyor status](https://ci.appveyor.com/api/projects/status/68muap4s7ijlr8aj/branch/master?svg=true)](https://ci.appveyor.com/project/mcg1969/nb-conda-kernels) | [![Anaconda-Server Badge](https://anaconda.org/jupycon/nb_conda_kernels/badges/latest_release_date.svg)](https://anaconda.org/jupycon/nb_conda_kernels) |
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

### Limitations

This extension works _only_ with Jupyter notebooks and
JupyterLab. Unfortunately, it does not currently work with
Jupyter Console, `nbconvert`, and other tools. This is because
these tools were not designed to allow for the use of custom
KernelSpecs.

A new [kernel discovery system](https://jupyter-client.readthedocs.io/en/latest/kernel_providers.html)
is being developed for Jupyter 6.0 that should enable the
wider Jupyter ecosystem to take advantage of these external
kernels. This package will require modification to
function properly in this new system.

## Configuration

This package introduces two additional configuration options:

- `env_filter`: Regex to filter environment path matching it. Default: `None` (i.e. no filter)
- `name_format`: String name format; `'{0}'` = Language, `'{1}'` = Kernel. Default: `'{0} [conda env:{1}]'`

In order to pass a configuration option in the command line use ```python -m nb_conda_kernels list --CondaKernelSpecManager.env_filter="regex"``` where regex is the regular expression for filtering envs "this|that|and|that" works.
To set it in jupyter config file, edit the jupyter configuration file (py or json) located in your ```jupyter --config-dir```
- for `jupyter_notebook_config.py` - add a line "c.CondaKernelSpecManager.env_filter = 'regex'"
- for `jupyter_notebook_config.json` - add a json key 
```{
  "CondaKernelSpecManager": {
    "env_filter": "regex"
  ```

- ```python -m nb_conda_kernels list``` does not seem to process jupyter config files
* filter does not seem to filter out kernels installed with --user, local kernel of the jupyter env, or root kernels

## Development

1. Install [Anaconda](https://www.anaconda.com/download/) or
   [Miniconda](https://conda.io/miniconda.html).

2. Create a development environment.

   ```shell
   conda create -n nb_conda_kernels pip python=YOUR_FAVORITE_PYTHON
   # Linux / Mac
   conda activate nb_conda_kernels
   # Windows
   activate nb_conda_kernels
   # Install the package and test dependencies
   conda install --file requirements.txt
   ```

3. Install the source package in development mode.

   ```shell
   pip install -e .
   python -m nb_conda_kernels.install --enable
   ```

   Note: there is no longer any need to supply a
   `--prefix` argument to the installer.

4. In order to properly exercise the package, the
   tests assume a number of requirements:
   - `ipykernel` in the base/root environment
   - one additional environment with `ipykernel`
   - one environment with `r-irkernel`
   - one environment with a space in the name
   - one environment with a non-ASCII character in the name

   An easy way to accomplish this is to use the environment
   specifications in the `conda-recipe` directory:
   ```shell
   conda install -n root ipykernel
   conda env create -f conda-recipe/testenv1.yaml
   conda env create -f conda-recipe/testenv2.yaml
   ```

5. To run all of the tests, run the command `pytest -m nb_conda_kernels`.

## Changelog

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
