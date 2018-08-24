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
It should be installed in then environment from which
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


## Development

1. Install [Anaconda](https://www.anaconda.com/download/) or
   [Miniconda](https://conda.io/miniconda.html).

2. Create a development environment. Node.JS packages
   [PhantomJS](http://phantomjs.org) and
   [CasperJS](http://casperjs.org) are used for testing,
   so installation requires both `conda` and `npm`:
   ```shell
   conda create -n nb_conda_kernels python=YOUR_FAVORITE_PYTHON
   # Linux / Mac
   conda activate nb_conda_kernels
   # Windows
   activate nb_conda_kernels
   # Install the package and test dependencies
   conda install --file requirements.txt
   # Install PhantomJS and CasperJS
   npm install
   ```

3. Install the source package in development mode.
   ```shell
   python setup.py develop
   # Linux / Mac
   python -m nb_conda_kernels.install --enable --prefix="${CONDA_PREFIX}"
   # Windows
   python -m nb_conda_kernels.install --enable --prefix="%CONDA_PREFIX%"
   ```

4. In order to properly exercise the package, the
   tests assume the existence of `ipykernel` in the
   base/root conda environment, and at least one conda
   environment with the `R` kernel. For example:
   ```shell
   conda install -n root ipykernel
   conda create -n nbrtest r-irkernel
   ```

5. To run all of the tests, the Node environment must be
   activated. The easiest way to do this is to use our
   `npm` test command:
   ```shell
   npm run test
   ```
   If you prefer to skip the Node-based tests, you can run
   `nose` directly, skipping the `test_notebook` module:
   ```
   nosetests --exclude=test_notebook
   ```

## Changelog

### 2.2.0
- Perform full activation of kernel conda environments
- Discover kernels from their kernel specs, enabling the use
  of kernels besides Python and R

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
