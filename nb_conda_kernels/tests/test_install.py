import os
import sys
import json

from subprocess import check_output, STDOUT

STATUS = 'nb_conda_kernels status: '
CONFIG_STATUS = '  - notebook configuration: '
PATCH_STATUS = '  - jupyter_client patch: '
ENABLING = 'Enabling nb_conda_kernels for notebooks...'
DISABLING = 'Disabling nb_conda_kernels...'
PATCHING = 'Patching jupyter_client.kernelspec...'
ENABLED = 'ENABLED'
DISABLED = 'DISABLED'
NOTEBOOK = 'NOTEBOOKS ONLY'

if sys.platform.startswith('win'):
    PYTHON = os.path.join(sys.prefix, 'python.exe')
else:
    PYTHON = os.path.join(sys.prefix, 'bin', 'python')


def check_command_(command, outs, verbose=False):
    cmd = [PYTHON, '-m', 'nb_conda_kernels']
    if verbose:
        cmd.append('--verbose')
    cmd.append(command)
    print(' '.join(cmd))
    output = check_output(cmd, stderr=STDOUT).decode()
    print('\n'.join('| ' + x for x in output.splitlines()))
    for out in outs:
        assert out in output
    return output


def retrieve_state():
    output = check_command_('status', ())
    state = {
        'notebook': ENABLED if (CONFIG_STATUS + ENABLED) in output else DISABLED,
        'patch': ENABLED if (PATCH_STATUS + ENABLED) in output else DISABLED
    }
    return state


def restore_state(state):
    check_command_('disable', ())
    if state['notebook'] == ENABLED:
        check_command_('enable', ())
    if state['patch'] == ENABLED:
        check_command_('patch', ())


def test_install():
    for verbose in (False, True):
        original_state = retrieve_state()
        predicted_state = original_state.copy()
        for test in ('disable', 'status', 'disable', 'status',
                     'enable', 'status', 'enable', 'status', 'disable', 'status',
                     'patch', 'status', 'patch', 'status', 'unpatch', 'status',
                     'enable', 'status', 'patch', 'status', 'disable', 'status'):
            if test == 'disable':
                predicted_state['notebook'] = predicted_state['patch'] = DISABLED
            elif test == 'patch':
                predicted_state['patch'] = ENABLED
            elif test == 'unpatch':
                predicted_state['patch'] = DISABLED
            elif test == 'enable' and predicted_state['patch'] == DISABLED:
                predicted_state['notebook'] = ENABLED
            if predicted_state['patch'] == ENABLED:
                predicted_status = ENABLED
            elif predicted_state['notebook'] == ENABLED:
                predicted_status = NOTEBOOK
            else:
                predicted_status = DISABLED
            check_command_(test, (STATUS + predicted_status,
                                  CONFIG_STATUS + predicted_state['notebook'],
                                  PATCH_STATUS + predicted_state['patch']),
                           verbose=verbose)
        restore_state(original_state)


def test_patch():
    original_state = retrieve_state()
    check_command_('patch', ())
    cmd = [PYTHON, '-m', 'jupyter', 'kernelspec', 'list', '--json']
    jupyter_specs = json.loads(check_output(cmd).decode('ascii'))['kernelspecs']
    from nb_conda_kernels.manager import CondaKernelSpecManager
    my_specs = CondaKernelSpecManager().get_all_specs()
    assert jupyter_specs == my_specs, (jupyter_specs, my_specs)
    restore_state(original_state)


if __name__ == '__main__':
    test_install()
    test_patch()
