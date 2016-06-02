# nb_conda_kernels
Manage your `conda` environment-based kernels inside the Jupyter Notebook.

This package defines a custom KernelSpecManager that automatically
creates KernelSpecs for each conda environment. When you create a new
notebook, you can choose a kernel corresponding to the environment
you wish to run within. This will allow you to have different versions
of python, libraries, etc. for different notebooks.

## Installation
```shell
conda install -c conda-forge nb_conda_kernels
```


### Getting Started
You'll need conda installed, either from [Anaconda](https://www.continuum.io/downloads) or [miniconda](http://conda.pydata.org/miniconda.html). You can create a Python development environment named `nb_conda_kernels` from `./environment.yml`.

```shell
conda create -n nb_conda_kernels python=YOUR_FAVORITE_PYTHON
conda update env
source activate nb_conda_kernels
python setup.py develop
python -m nb_conda_kernels.install --enable --prefix="${CONDA_ENV_PATH}"
```

We _still_ use `npm` for testing things, so then run:
```shell
npm install
```

Finally, you are ready to run the tests!
```shell
npm run test
```


## Changelog

### 1.0.2
- use [Travis-CI](https://travis-ci.org/Anaconda-Platform/nb_conda_kernels) for continuous integration
- use [Coveralls](https://coveralls.io/github/Anaconda-Platform/nb_conda_kernels) for code coverage
- use a [conda-forge](https://github.com/conda-forge/nb_conda_kernels-feedstock) for cross-platform `conda` package building

### 1.0.1
- minor build changes

### 1.0.0
- update to notebook 4.2
