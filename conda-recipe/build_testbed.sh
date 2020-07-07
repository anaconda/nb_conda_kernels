#!/bin/bash

# Requirements:
# -- CONDA_ROOT should be in a fixed location throughout the job.
#    On a Mac, GITHUB_WORKSPACE seems to change from task to task so
#    anything relative to that directory will not work
# -- CONDA_ROOT should be on the same filesystem as GITHUB_WORKSPACE
#    for performance. $HOME does not satisfy this on Windows
# -- CONDA_ROOT should not be within GITHUB_WORKSPACE, lest conda
#    build copy the entire directory into the package build workspace
# Solution: $HOME/conda for Unix; D:\conda for Windows
# On the other hand, actions/cache cannot cache content outside of
if [ "$RUNNER_OS" == "Windows" ]; then
    CONDA_ROOT="${GITHUB_WORKSPACE%\\*\\*}\\conda"
else
    CONDA_ROOT="$HOME/conda"
fi
# This makes CONDA_ROOT available to subsequent steps
echo "::set-env name=CONDA_ROOT::${CONDA_ROOT}"
echo "Conda testbed location: $CONDA_ROOT"

# Exit quickly if the cached version is available. See the end of
# the script for the explanation why we do it this way
if [ -d $GITHUB_WORKSPACE/conda/conda-meta ]; then
    echo "Cached copy has been retrieved; moving into place"
    rm -rf $CONDA_ROOT
    mkdir -p ~/.conda
    mv $GITHUB_WORKSPACE/conda $CONDA_ROOT
    mv $CONDA_ROOT/environments.txt ~/.conda
    conda info -a
    exit 0
fi

# Use the built-in conda to create our new conda testbed
# We need to move the package cache to a writable location on the Mac
# to work around an issue with GitHub's implementation. And this has
# the nice side effect of reducing the size of our conda tree, too
[ "$RUNNER_OS" == "Windows" ] && CONDA_E="$CONDA/Scripts/conda.exe"
[ "$RUNNER_OS" != "Windows" ] && CONDA_E=conda
$CONDA_E config --add pkgs_dirs ~/.pkgs
$CONDA_E create -p $CONDA_ROOT conda

# We need to create additional environments to fully test the logic,
# including an R kernel, a Python kernel, and environment names with at
# least one non-ASCII character and one space. We also need one environment
# installed in a non-default environment location.     
cwd=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)
source $CONDA_ROOT/etc/profile.d/conda.sh
conda install -y conda-build conda-verify ipykernel
conda env create -f $cwd/testenv1.yaml
conda env create -f $cwd/testenv2.yaml
mkdir -p $CONDA_ROOT/ext1/ext2/env
conda env create -f $cwd/testenv1.yaml -p $CONDA_ROOT/ext1/ext2/env/test_env1

# Display final result
conda info -a

# If an argument has been supplied, it means that we are inside the
# testbed job, whose purpose is simply to cache this work with the
# actions/cache action. Unfortunately, this action does not reliably
# cache assets that sit outside of GITHUB_WORKSPACE. So we move it
# in there before caching, and move it out after retrieval.
if [ "$@" ]; then
    echo "Moving environment into cache position"
    rm -rf $GITHUB_WORKSPACE/conda
    mv ~/.conda/environments.txt $CONDA_ROOT
    mv $CONDA_ROOT $GITHUB_WORKSPACE/conda
fi
