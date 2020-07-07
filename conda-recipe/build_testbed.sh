#!/bin/bash

# GitHub action specific items. These are no-ops locally
[ "$RUNNER_OS" == "Windows" ] && CONDA_EXE="$CONDA/Scripts/conda.exe"
[ "$RUNNER_OS" == "macOS" ] && export CONDA_PKGS_DIRS=~/.pkgs

cwd=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)

if [[ "$CONDA_ROOT" != "" ]]; then
    mkdir -p $CONDA_ROOT
    croot=$(cd $CONDA_ROOT && pwd)
else
    croot=${cwd%/*}/conda
fi

# Exit quickly if the cached version is available. See the end of
# the script for the explanation why we do it this way
if [ -d $croot/conda-meta ]; then
    source $croot/etc/profile.d/conda.sh
    mkdir -p ~/.conda
    cp $croot/environments.txt ~/.conda
    conda info
    conda info --envs
    exit 0
fi

# Create the root environment
${CONDA_EXE:-conda} create -y -p $croot conda python=3.7

# We need to create additional environments to fully test the logic,
# including an R kernel, a Python kernel, and environment names with at
# least one non-ASCII character and one space. We also need one environment
# installed in a non-default environment location.     
source $croot/etc/profile.d/conda.sh
conda install -y conda-build conda-verify ipykernel
conda env create -f $cwd/testenv1.yaml
conda env create -f $cwd/testenv2.yaml
mkdir -p $CONDA_ROOT/ext1/ext2/env
conda env create -f $cwd/testenv1.yaml -p $CONDA_ROOT/ext1/ext2/env/test_env1
rm -rf $croot/pkgs

# Display final result
conda info
conda info --envs
