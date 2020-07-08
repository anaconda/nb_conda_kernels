import os
import sys

from subprocess import check_output, call, STDOUT

STATUS = 'Determining the status of nb_conda_kernels...'
ENABLING = 'Enabling nb_conda_kernels...'
DISABLING = 'Disabling nb_conda_kernels...'
IS_ENABLED = 'Status: enabled'
IS_DISABLED = 'Status: disabled'

if sys.platform.startswith('win'):
    PYTHON = os.path.join(sys.prefix, 'python.exe')
else:
    PYTHON = os.path.join(sys.prefix, 'bin', 'python')


def check_command_(command, out1, out2, verbose=False, quiet=False):
    cmd = [PYTHON, '-m', 'nb_conda_kernels.install', '--' + command]
    if verbose:
        cmd.append('--verbose')
    print('Testing: {}'.format(' '.join(cmd)))
    output = check_output(cmd, stderr=STDOUT).decode()
    print('\n'.join('| ' + x for x in output.splitlines()))
    if not quiet:
        assert out1 in output
        assert out2 in output


def test_install():
    call([PYTHON, '-m', 'nb_conda_kernels.install', '--enable'])
    for verbose in (False, True):
        for test in (('status', STATUS, IS_ENABLED),
                     ('disable', DISABLING, IS_DISABLED),
                     ('status', STATUS, IS_DISABLED),
                     ('enable', ENABLING, IS_ENABLED),
                     ('status', STATUS, IS_ENABLED)):
            print(test)
            check_command_(*test, verbose=verbose, quiet=False)


if __name__ == '__main__':
    test_install()
