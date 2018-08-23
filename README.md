# nb_conda_kernels
Manage your `conda` environment-based kernels inside the Jupyter Notebook.

This package defines a custom KernelSpecManager that automatically
creates KernelSpecs for each conda environment. When you create a new
notebook, you can choose a kernel corresponding to the environment
you wish to run within. This will allow you to have different versions
of python, libraries, etc. for different notebooks.

**Important Note** : To use a Python kernel from a conda environment,
don't forget to install `ipykernel` in that environment or it won't
show up on the kernel list. Similary, to use an R kernel, install
`r-irkernel`.

## Installation
```shell
conda install nb_conda_kernels
```

### Getting Started
You'll need conda installed, either from [Anaconda](https://www.continuum.io/downloads) or [miniconda](http://conda.pydata.org/miniconda.html). 

```shell
conda create -n nb_conda_kernels nb_conda_kernels python=YOUR_FAVORITE_PYTHON
conda activate nb_conda_kernels
# Remove just the package, leave the dependencies
conda remove nb_conda_kernels --force
# Install the test packages
conda install --file requirements.txt
python setup.py develop
python -m nb_conda_kernels.install --enable --prefix="${CONDA_PREFIX}"
# or on windows
python -m nb_conda_kernels.install --enable --prefix="%CONDA_PREFIX%"
```
The tests assume the existence of `ipykernel` in the
base/root conda environment, and at least one conda
environment with the `R` kernel; e.g.
```shell
conda install -n root ipykernel
conda create -n nbrtest r-irkernel
```

To run all of the tests, you need to use node:
```shell
npx -p casperjs -p phantomjs nosetests
```
However, only the `test_notebook` module requires node, so to
skip that test and run the others, you could do:
```
nosetests --exclude=test_notebook
```


## Changelog

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
