#!/usr/bin/env python
# coding: utf-8

# Copyright (c) - Continuum Analytics

from __future__ import print_function

# the name of the project
name = 'nb_conda_kernels'

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,4)):
    error = "ERROR: %s requires Python version 2.7 or 3.4 or above." % name
    print(error, file=sys.stderr)
    sys.exit(1)

#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------

import os
from glob import glob

from distutils.core import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, name)

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

version_ns = {}
with open(pjoin(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)

setup_args = dict(
    name            = name,
    version         = version_ns['__version__'],
    packages        = packages,
    #description     = "",
    #long_description= """
    #""",
    #author          = '',
    #author_email    = '',
    #url             = '',
    #license         = '',
    platforms       = "Linux, Mac OS X, Windows",
    #keywords        = [],
    #classifiers     = [],
    #cmdclass        = []
)

if 'develop' in sys.argv or any(bdist in sys.argv for bdist in ['bdist_wheel', 'bdist_egg']):
    import setuptools

setuptools_args = {}

REQUIRES = [
    'nb_config_manager',
    'traitlets>=4.1.0',
]

install_requires = setuptools_args['install_requires'] = REQUIRES

if 'setuptools' in sys.modules:
    setup_args.update(setuptools_args)

if __name__ == '__main__':
    setup(**setup_args)
