import re
import pkgutil
import logging
import os
import sys
import stat

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
           ['| ' + p for p in str(exc).splitlines()] +
           ['nb_conda_kernels NOT loaded; please reinstall.'])
    warnings.warn('\\n'.join(msg))
finally:
    del NBCK_modver, CondaKernelSpecManager
'''.format(VERSION)

NEW_PREFIX = '.nbck_new'
OLD_PREFIX = '.nbck_old'
OS_FLAGS = os.O_CREAT | os.O_WRONLY | os.O_EXCL
if hasattr(os, 'O_BINARY'):
    OS_FLAGS |= os.O_BINARY


def notify(level, text):
    notifier = getattr(log, level)
    return notifier('{}: {}'.format(level.upper(), text))


def find_compatible_jc_version(level='info'):
    p = pkgutil.get_loader('jupyter_client._version')
    if p is None:
        notify(level, 'Cannot find module jupyter_client._version')
        return None
    v_mod = p.load_module()
    version = getattr(v_mod, 'version_info', None)
    if version is None:
        notify(level, 'Cannot determine jupyter_client._version')
    elif not isinstance(version, tuple):
        notify(level, 'Cannot parse jupyter_client version: {}'.format(repr(version)))
    elif version < (5,) or version >= (6,):
        version_str = '.'.join(map(str, version))
        notify(level, 'jupyter_client version {} incompatible with patch'.format(version_str))
    else:
        return True
    return False


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
    patch_match = re.match(patch_finder.encode('ascii'), fdata, re.MULTILINE | re.DOTALL)
    if not patch_match:
        log.debug('No patch code found.')
        return fdata, 0
    log.debug('Patch code found.')
    groups = patch_match.groups()
    fdata = groups[0] + groups[2]
    version_finder = '.* NBCK_modver == (\d+)'
    version_match = re.match(version_finder.encode('ascii'), groups[1], re.MULTILINE | re.DOTALL)
    if not version_match:
        log.debug('Could not determine the patch version.')
        return fdata, -1
    version = int(version_match.groups()[0])
    log.debug('Patch version: {}'.format(version))
    return fdata, version


def status(level='warning'):
    """Determines whether or not the jupyter_client patch is applied.
       Returns True if the patch is applied *and* it is the correct
       version of the patch; False otherwise."""
    log.debug('Examining jupyter_client.kernelspec')
    if not find_compatible_jc_version(level):
        return False
    fname = find_kernelspec_py()
    fdata, NL = read_kernelspec_py(fname)
    _, version = determine_kernelspec_py_status(fdata, NL)
    return version == VERSION


def attempt_remove(fname, ftext, must_succeed=True):
    if os.path.exists(fname):
        try:
            log.debug('Removing {}'.format(ftext))
            os.remove(fname)
        except OSError:
            if must_succeed:
                raise
            log.warn('Could not remove: {}'.format(fname))


def patch(uninstall=False):
    """Overwrites the current file with a patched/unpatched version.
       Attempts to be as safe as possible, first writing the results to
       a temporary file, verifying that file's contents, and only then
       moving the new file into place."""

    log.debug('{}ing the patch...'.format('Remov' if uninstall else 'Apply'))
    if not find_compatible_jc_version('error'):
        return False
    fname = find_kernelspec_py()
    fdata_orig, NL = read_kernelspec_py(fname)
    fdata_cleaned, current_version = determine_kernelspec_py_status(fdata_orig, NL)
    if current_version == (0 if uninstall else VERSION):
        log.debug('No changes needed.')
        return True

    if uninstall:
        fdata_new = fdata_cleaned
    else:
        parts = [HEADER] + PATCH_CODE.splitlines() + [FOOTER, '']
        parts = [fdata_cleaned] + [x.encode('ascii') for x in parts]
        fdata_new = NL.encode('ascii').join(parts)

    fname_new = fname + NEW_PREFIX
    fname_old = fname + OLD_PREFIX

    try:
        log.debug('Determining file permissions')
        stat_res = os.stat(fname)
        file_perms = stat.S_IMODE(stat_res.st_mode)
        log.debug('File permissions: {}'.format(file_perms))

        attempt_remove(fname_new, 'previous staging file', True)
        log.debug('Creating staging file')
        with open(fname_new, 'w+b') as fp:
            fp.write(fdata_new)
        os.chmod(fname_new, file_perms)

        log.debug('Verifying staging file')
        fdata_read, NL = read_kernelspec_py(fname_new)
        if fdata_read != fdata_new:
            raise RuntimeError('Write verification failed')
        fdata_stripped, version_new = determine_kernelspec_py_status(fdata_new, NL)
        if version_new != (0 if uninstall else VERSION):
            raise RuntimeError('Version verification failed')
        if fdata_stripped != fdata_cleaned:
            raise RuntimeError('Original file integrity check failed')

        log.debug('Moving staging file into position')
        if hasattr(os, 'replace'):
            os.replace(fname_new, fname)
        elif sys.platform.startswith('win'):
            # No atomic replace on Windows Python 2.7
            attempt_remove(fname_old, 'previous backup file', True)
            os.rename(fname, fname_old)
            os.rename(fname_old, fname_new)
        else:
            os.rename(fname_new, fname)
        return True

    except Exception:
        msg = 'NOTE: the original kernelspec.py file has NOT been modified.'
        if os.path.exists(fname_old) and not os.path.exists(fname):
            try:
                os.rename(fname_old, fname)
            except OSError:
                # We should never get here. But if we do, let's have full disclosure
                msg = ('**** IMPORTANT NOTE ****\n'
                       'The original kernelspec.py cannot be restored.\n'
                       'It will be necessary to reinstall the jupyter_client package.')
        log.error(msg)
        raise

    finally:
        attempt_remove(fname_old, 'backup file', False)
        attempt_remove(fname_old, 'staging file', False)
