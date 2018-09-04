#!/usr/bin/env python
# coding: utf-8

# Copyright (c) - Continuum Analytics

import re
import pkgutil
import argparse
import tempfile
import os
from os.path import exists, join, basename
import logging

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

# Arguments for command line
parser = argparse.ArgumentParser(
    description="Patches jupyter_client.kernelspec to enable conda kernels")
parser.add_argument(
    "-e", "--enable",
    help="Enables loading nb_conda_kernels on notebook/console launch",
    action="store_true")
parser.add_argument(
    "-d", "--disable",
    help="Disables loading nb_conda_kernels on notebook/console launch",
    action="store_true")
parser.add_argument(
    "-v", "--verbose",
    help="Show more output",
    action="store_true"
)

VERSION = 1
VERSION_LEAD = '### Version '
HEADER = '### BEGIN NB_CONDA_KERNELS PATCH ###'
FOOTER = '### END NB_CONDA_KERNELS_PATCH ###'
PATCH_CODE = '''
try:
    from nb_conda_kernels.manager import CondaKernelSpecManager
    KernelSpecManager = CondaKernelSpecManager
except ImportError:
    pass
'''


def find_kernelspec():
    log.info('Looking for jupyter_client.kernelspec')
    try:
        p = pkgutil.get_loader('jupyter_client.kernelspec')
    except ImportError:
        log.info('No jupyter_client.kernelspec module was found.')
        return None, None, None
    return getattr(p, 'filename', None) or getattr(p, 'path')


def read_kernelspec(fname):
    log.info('    {}'.format(fname))
    with open(fname, 'rb') as fp:
        fdata = fp.read()
    for NL in ('\r\n', '\n', '\r'):
        if NL.encode('ascii') in fdata:
            break
    else:
        raise RuntimeError('Could not determine the newline format for the kernelspec file')
    log.info('    Newline format: {}'.format(repr(NL)))
    return fdata, NL


def determine_kernelspec_status(fdata, NL):
    log.info('Searching for patch code')
    patch_finder = '(.*){}{}{}(.*){}{}{}(.*)'.format(NL, HEADER, NL, NL, FOOTER, NL)
    patch_match = re.match(patch_finder.encode('ascii'), fdata, re.MULTILINE|re.DOTALL)
    if not patch_match:
        log.info('No nb_conda_kernels patch code found.')
        return fdata, 0
    log.info('nb_conda_kernels patch code found!')
    groups = patch_match.groups()
    fdata = groups[0] + groups[2]
    version_finder = '^{}(\d+)'.format(VERSION_LEAD)
    version_match = re.match(version_finder.encode('ascii'), groups[1])
    if not version_match:
        log.info('Could not determine the patch version.')
        return fdata, -1
    version = int(version_match.groups()[0])
    log.info('Patch version: {}'.format(version))
    return fdata, version


def rewrite_kernelspec(fname, fdata_patched, fdata_orig, fdata_cleaned):
    log.info('Opening temporary file')
    fp = tempfile.NamedTemporaryFile(prefix=fname + '.', delete=False)
    tname = fp.name
    fp.write(fdata_patched)
    fp.close()
    log.info('Moving temporary file into position')
    try:
        os.rename(tname, fname)
    except OSError as exc:
        log.info('Could not replace file; attempting to remove temporary')
        try:
            os.remove(tname)
        except OSError as exc:
            log.info('Could not remove temporary file: {}'.format(exc.message))
            pass
        raise exc
    log.info('Verifying new file')
    with open(fname, 'rb') as fp:
        fdata_new = fp.read()
    if fdata_new == fdata_patched:
        log.info('Modified file verified.')
        return fdata_new
    elif fdata_new == fdata_orig:
        raise RuntimeError('Unexpected error; kernelspec.py NOT MODIFIED.')
    elif fdata_new == fdata_cleaned:
        raise RuntimeError('Unexpected error; kernelspec.py returned to UNPATCHED state.')
    raise RuntimeError('Unexpected error; PLEASE INSPECT kernelspec.py:\n    {}'.format(fname))


def status():
    fname = find_kernelspec()
    if fname is None:
        print('No jupyter_client.kernelspec module was found.')
    fdata, NL = read_kernelspec(fname)
    fdata_cleaned, version = determine_kernelspec_status(fdata, NL)
    if version == 0:
        print('No patch code found.')
    elif version == -1:
        print('Patch version could not be determined.')
    else:
        print('Patch version {} found.'.format(version))
    return 0


def patch(target):
    fname = find_kernelspec()
    if fname is None:
        raise RuntimeError('Could not find the jupyter_client.kernelspec module')
    fdata_orig, NL = read_kernelspec(fname)
    fdata_cleaned, version = determine_kernelspec_status(fdata_orig, NL)
    if version == target:
        if target:
            log.info('Correct version of patch already applied.')
        else:
            log.info('No patch code was found; no modification needed.')
        return 0
    elif target:
        if version == -1:
            log.info('Unknown patch version detected; attempting to re-patch.')
        elif version == 0:
            log.info('No patch code was found; attempting to patch.')
        else:
            log.info('Patch version mismatch ({} != {}); attempting to re-patch.'.format(version, target))
        parts = [ HEADER, VERSION_LEAD + str(VERSION) ] + PATCH_CODE.splitlines() + [ FOOTER, '' ]
        parts = [ fdata_cleaned ] + [ x.encode('ascii') for x in parts ]
        fdata_patched = NL.encode('ascii').join(parts)
    else:
        log.info('Patch code found; attempting removal.')
        fdata_patched = fdata_cleaned
    fdata_new = rewrite_kernelspec(fname, fdata_patched, fdata_orig, fdata_cleaned)
    fdata_recleaned, version = determine_kernelspec_status(fdata_new, NL)
    if version != target:
        raise RuntimeError('Unexpected error reading patched kernelspec code; please examine:\n   {}'.format(fname))
    log.info('Patch successfully {}.'.format('applied' if target else 'removed'))
    if fdata_recleaned != fdata_cleaned:
        log.info('WARNING: round-trip issue cleaning the code')
    return 0


if __name__ == '__main__':
    args = parser.parse_args()
    if verbose:
        log.setLevel(logging.DEBUG)
    if not enable and not disable:
        log.error('Please provide one of: --enable, --disable')
        raise ValueError(enable, disable)
    if enable and disable
        log.error('Must not provide both --enable and --disable')
        raise ValueError(enable, disable)
