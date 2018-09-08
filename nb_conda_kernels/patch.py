import re
import pkgutil
import logging
import tempfile
import os
import sys

from os.path import exists, join, basename

log = logging.getLogger('nb_conda_kernels')


VERSION = 2
HEADER = '### BEGIN NB_CONDA_KERNELS PATCH ###'
FOOTER = '### END NB_CONDA_KERNELS_PATCH ###'
PATCH_CODE = '''try:
    NBCK_modver = CondaKernelSpecManager = None
    from nb_conda_kernels.patch import VERSION as NBCK_modver
    from nb_conda_kernels.manager import CondaKernelSpecManager
    if NBCK_modver == {} and CondaKernelSpecManager is not None:
        KernelSpecManager = CondaKernelSpecManager
except Exception as exc:
    msg = (['Unexpected error attempting to use nb_conda_kernels:'] +
           ['| ' + p for p in exc.message.splitlines()] +
           ['nb_conda_kernels NOT loaded; please reinstall.'])
    warnings.warn('\\n'.join(msg))
finally:
    del NBCK_modver, CondaKernelSpecManager
'''.format(VERSION)


def find_kernelspec_py():
    """Return the path to the source file for jupyter_client.kernelspec."""
    p = pkgutil.get_loader('jupyter_client.kernelspec')
    fname = getattr(p, 'filename', None) or getattr(p, 'path')
    return fname


def read_kernelspec_py(fname, expected=None):
    """Read the given text file and return its contents and the detected newline
       convention used within. The file is read in binary mode to better ensure
       round-trip integrity when patching."""
    log.debug('Reading: {}'.format(fname))
    with open(fname, 'rb') as fp:
        fdata = fp.read()
    if expected is not None:
        assert fdata == expected
    for NL in ('\r\n', '\n', '\r'):
        if NL.encode('ascii') in fdata:
            break
    else:
        raise RuntimeError('Could not determine the newline format for the kernelspec file')
    log.debug('Detected newline format: {}'.format(repr(NL)))
    return fdata, NL


def determine_kernelspec_py_status(fdata, NL):
    """Examines the text data (still represented as binary) for the
       presence of an instance of the patch code. If the patch is not
       found, the full data is returned and a 0 value. If patch data
       is detected, returns the text *with the patch removed*, and the
       version of the patch found."""
    patch_finder = '(.*){}{}{}(.*){}{}{}(.*)'.format(NL, HEADER, NL, NL, FOOTER, NL)
    patch_match = re.match(patch_finder.encode('ascii'), fdata, re.MULTILINE|re.DOTALL)
    if not patch_match:
        log.debug('No patch code found.')
        return fdata, 0
    log.debug('Patch code found.')
    groups = patch_match.groups()
    fdata = groups[0] + groups[2]
    version_finder = '.* NBCK_modver == (\d+)'
    version_match = re.match(version_finder.encode('ascii'), groups[1], re.MULTILINE|re.DOTALL)
    if not version_match:
        log.debug('Could not determine the patch version.')
        return fdata, -1
    version = int(version_match.groups()[0])
    log.debug('Patch version: {}'.format(version))
    return fdata, version


def status():
    """Determines whether or not the jupyter_client patch is applied.
       Returns True if the patch is applied *and* it is the correct
       version of the patch; False otherwise."""
    log.debug('Examining jupyter_client.kernelspec')
    fname = find_kernelspec_py()
    fdata, NL = read_kernelspec_py(fname)
    _, version = determine_kernelspec_py_status(fdata, NL)
    return version == VERSION


def patch(uninstall=False):
    """Overwrites the current file with a patched/unpatched version.
       Attempts to be as safe as possible, first writing the results to
       a temporary file, verifying that file's contents, and only then
       moving the new file into place."""

    log.debug('{}ing the patch...'.format('Remov' if uninstall else 'Apply'))
    fname = find_kernelspec_py()
    fdata_orig, NL = read_kernelspec_py(fname)
    fdata_cleaned, current_version = determine_kernelspec_py_status(fdata_orig, NL)
    if current_version == (0 if uninstall else VERSION):
        log.debug('No changes needed.')
        return

    if uninstall:
        fdata_new = fdata_cleaned
    else:
        parts = [ HEADER ] + PATCH_CODE.splitlines() + [ FOOTER, '' ]
        parts = [ fdata_cleaned ] + [ x.encode('ascii') for x in parts ]
        fdata_new = NL.encode('ascii').join(parts)

    try:
        log.debug('Constructing new file')
        fp = tempfile.NamedTemporaryFile(mode='w+b', prefix=fname + '.', delete=False)
        tname = fp.name
        log.debug('Temporary file name: {}'.format(tname))
        fp.write(fdata_new)
        fp.close()

        log.debug('Verifying new file')
        fdata_read, NL = read_kernelspec_py(tname)
        if fdata_read != fdata_new:
            raise RuntimeError('Write verification failed')

        fdata_stripped, version_new = determine_kernelspec_py_status(fdata_new, NL)
        if version_new != (0 if uninstall else VERSION):
            raise RuntimeError('Version verification failed')
        if fdata_stripped != fdata_cleaned:
            raise RuntimeError('Original file integrity check failed')

        log.debug('Modified file verified; moving into position')
        os.rename(tname, fname)

    except Exception as exc:
        msg = (['Unexpected error during the patching process:'] +
               ['| ' + p for p in exc.message.splitlines() ] +
               ['The original kernelspec.py file has NOT been modified.'])
        raise type(exc)('\n'.join(msg))

    finally:
        if tname and os.path.exists(tname):
            log.debug('Attempting to remove temporary')
            try:
                os.remove(tname)
            except OSError as exc:
                log.warn('Could not remove temporary file: {}'.format(exc.message))


