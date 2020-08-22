#!/bin/bash

# GitHub action specific items. These are no-ops locally
[ "$RUNNER_OS" == "Windows" ] && CONDA_EXE="$CONDA/Scripts/conda.exe"
[ "$RUNNER_OS" == "macOS" ] && export CONDA_PKGS_DIRS=~/.pkgs

# Determine the root location of the testbed
cwd=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)
[ $CONDA_ROOT ] || CONDA_ROOT=${cwd%/*/*}/nbckdev
mkdir -p $CONDA_ROOT
export CONDA_ROOT=$(cd $CONDA_ROOT && pwd)
echo "Testbed location: $CONDA_ROOT"

function full_deactivate {
    old_prefix=${CONDA_EXE%/*/*}
    if [ -d "$old_prefix/conda-meta" ]; then
        old_source=$old_prefix/etc/profile.d/conda.sh
        source $old_source && conda deactivate
        new_path=$(echo $PATH | tr ':' '\n' | grep -v "^$old_prefix/" | tr '\n' ':')
        export PATH=${new_path%:}
    fi
}

# Skip creation if the cached version is available
if [ ! -d $CONDA_ROOT/conda-meta ]; then
    ${CONDA_EXE:-conda} env create -f $cwd/croot.yml -p $CONDA_ROOT
    if [[ "$RUNNER_OS" == "" && "$OS" == "Windows_NT" ]]; then
        conda install -y -p $CONDA_ROOT m2-bash m2-coreutils m2-filesystem
    fi
fi

full_deactivate
source $CONDA_ROOT/etc/profile.d/conda.sh
conda activate base

if [ ! -f $CONDA_ROOT/.created ]; then
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

    touch $CONDA_ROOT/.created
fi

# Make sure the external environment is in the environments.txt file
ext_env=$CONDA_ROOT/ext1/ext2/env/test_env1
if [ "$OS" == "Windows_NT" ]; then
    CONDA_HOME=$USERPROFILE
    ext_env=$(echo $ext_env | sed -E 's@^/([^/]*)@\U\1:@;s@/@\\@g')
    ext_env_g=^$(echo $ext_env | sed -E 's@\\@\\\\@g')
else
    CONDA_HOME=$HOME
    ext_env_g=^$ext_env
fi
if ! grep -q "$ext_env_g" $CONDA_HOME/environments.txt 2>/dev/null; then
    mkdir -p $CONDA_HOME/.conda
    echo "$ext_env" >> $CONDA_HOME/.conda/environments.txt
fi

# Display final result
echo PATH=$PATH
env | grep ^CONDA
conda info --envs
