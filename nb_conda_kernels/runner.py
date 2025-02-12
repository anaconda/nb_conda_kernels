from __future__ import print_function

import os
from os.path import join, exists
import sys
import subprocess
import locale
try:
    from shlex import quote
except ImportError:
    from pipes import quote


def exec_in_env(conda_prefix, env_path, *command):
    # Run the standard conda activation script, and print the
    # resulting environment variables to stdout for reading.
    is_current_env = env_path == sys.prefix
    mamba_path = os.environ.get('MAMBA_EXE')
    if sys.platform.startswith('win'):
        if is_current_env:
            subprocess.Popen(list(command)).wait()
            return
        else:
            activate_path = join(conda_prefix, 'Scripts', 'activate.bat')
            if exists(activate_path):
                ecomm = [os.environ['COMSPEC'], '/S', '/U', '/C', '@echo', 'off', '&&',
                        'chcp', '65001', '&&', 'call', activate_path, env_path, '&&',
                        '@echo', 'CONDA_PREFIX=%CONDA_PREFIX%', '&&'] + list(command)
                subprocess.Popen(ecomm).wait()
            return
    else:
        if is_current_env:
            os.execvp(command[0], list(command))
        activate = None
        env_path = quote(env_path)
        bin_path = join(conda_prefix, "bin")
        if mamba_path and exists(mamba_path):
            activate = 'eval "$({} shell activate {} --shell posix)"'.format(quote(mamba_path), env_path)
        elif exists(join(bin_path, "activate")) and not os.environ.get('NBCK_NO_ACTIVATE_SCRIPT'):
            activate = '. {}/activate {}'.format(quote(bin_path), env_path)
        elif exists(join(bin_path, "conda")):
            activate = 'eval "$({}/conda shell.posix activate {})"'.format(quote(bin_path), env_path)
        if activate:
            ecomm = (activate + '\nexec ') + ' '.join(quote(c) for c in command)
            print(ecomm, file=sys.stderr)
            ecomm = ['sh' if 'bsd' in sys.platform else 'bash', '-c', ecomm]
            os.execvp(ecomm[0], ecomm)

    raise RuntimeError('Could not determine an activation method')


if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
