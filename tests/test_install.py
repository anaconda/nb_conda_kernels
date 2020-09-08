import os
import sys

from subprocess import check_output, call, STDOUT

IS_ENABLED = 'Status: enabled'
IS_DISABLED = 'Status: disabled'

if sys.platform.startswith('win'):
    PYTHON = os.path.join(sys.prefix, 'python.exe')
else:
    PYTHON = os.path.join(sys.prefix, 'bin', 'python')


def check_command_(command, out, verbose=False, quiet=False):
    cmd = [PYTHON, '-m', 'nb_conda_kernels.install', '--' + command]
    if verbose:
        cmd.append('--verbose')
    print('Testing: {}'.format(' '.join(cmd)))
    output = check_output(cmd, stderr=STDOUT).decode()
    print('\n'.join('| ' + x for x in output.splitlines()))
    if not quiet:
        assert out in output


def test_install():
    call([PYTHON, '-m', 'nb_conda_kernels.install', '--enable'])
    for verbose in (False, True):
        for test in (('status',  IS_ENABLED),
                     ('disable', IS_DISABLED),
                     ('status',  IS_DISABLED),
                     ('enable',  IS_ENABLED),
                     ('status',  IS_ENABLED)):
            print(test)
            check_command_(*test, verbose=verbose, quiet=False)


if __name__ == '__main__':
    test_install()
