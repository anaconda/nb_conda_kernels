# nb_conda_kernels
Package for managing conda environment-based kernels inside of Jupyter

This package defines a custom KernelSpecManager that automatically
creates KernelSpecs for each conda environment. When you create a new
notebook, you can choose a kernel corresponding to the environment
you wish to run within. This will allow you to have different versions
of python, libraries, etc. for different notebooks.

To install: `conda install -c anaconda-nb-extensions nb_conda_kernels`
