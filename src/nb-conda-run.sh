#!/bin/bash
# Executes a single command in the given conda environment.
# Usage: nb-conda-run <conda-root> <env> <cmd> [<arg>...]
conda_root=$1
envname=$2
if [ "$envname" = "base" ]; then envname=root; fi
shift 2
source "$conda_root/bin/activate" "$envname" || exit $?
exec "$@"
