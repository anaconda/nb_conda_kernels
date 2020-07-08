#!/bin/bash

# GitHub action specific items. These are no-ops locally
[ "$RUNNER_OS" == "Windows" ] && CONDA_EXE="$CONDA/Scripts/conda.exe"
[ "$RUNNER_OS" == "macOS" ] && export CONDA_PKGS_DIRS=~/.pkgs

# Determine the root location of the testbed
cwd=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)
[ $CONDA_ROOT ] || CONDA_ROOT=${cwd%/*}/conda
mkdir -p $CONDA_ROOT
export CONDA_ROOT=$(cd $CONDA_ROOT && pwd)
echo "Testbed location: $CONDA_ROOT"

function finish {
    # Populate the environments.txt list if it doesn't exist
    # to make sure the off-location environment gets picked up
    conda info
    conda info --envs
    exit 0
}

# Exit quickly if the cached version is available. See the end of
# the script for the explanation why we do it this way
if [ -d $CONDA_ROOT/conda-meta ]; then
    source $CONDA_ROOT/etc/profile.d/conda.sh
    conda activate base
    finish
fi

${CONDA_EXE:-conda} env create -f $cwd/croot.yml -p $CONDA_ROOT
if [[ "$RUNNER_OS" == "" && "$OS" == "Windows_NT" ]]; then
	conda install -y -p $CONDA_ROOT m2-bash m2-coreutils m2-filesystem
fi
source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate base
echo "CONDA_ROOT: "$CONDA_ROOT
echo "CONDA_PREFIX: "$CONDA_PREFIX
pip install -e .
python -m nb_conda_kernels.install --enable

# We need to create additional environments to fully test the logic,
# including an R kernel, a Python kernel, and environment names with at
# least one non-ASCII character and one space. We also need one environment
# installed in a non-default environment location.     
conda env create -f $cwd/testenv1.yaml
conda env create -f $cwd/testenv2.yaml
mkdir -p $CONDA_ROOT/ext1/ext2/env
conda env create -f $cwd/testenv1.yaml -p $CONDA_ROOT/ext1/ext2/env/test_env1
rm -rf $CONDA_ROOT/pkgs

# Display final result
finish
