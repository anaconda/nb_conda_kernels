#!/bin/sh
# Executes a single command in the given conda environment.
# Usage: nb-conda-run <conda-root> <env> <cmd> [<arg>...]
conda_root=$1
shift
if [ "$1" = "base" ]; then envname=root; else envname=$1; fi
shift
. "$conda_root/bin/activate" "$envname" || exit $?
exec "$@"
