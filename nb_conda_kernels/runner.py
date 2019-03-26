from __future__ import print_function

import os
import sys
import shlex
import subprocess


def exec_in_env(conda_root, envname, *command):
    # Run the standard conda activation script, and print the
    # resulting environment variables to stdout for reading.
    envname = shlex.quote(envname)
    cmd_string = ' '.join(map(shlex.quote, command))
    if sys.platform.startswith('win'):
        activate = shlex.quote(os.path.join(conda_root, 'Scripts', 'activate.bat'))
        ecomm = 'call {} {} & {}'.format(activate, envname, cmd_string)
        subprocess.Popen(ecomm, shell=True).wait()
    else:
        activate = shlex.quote(os.path.join(conda_root, 'bin', 'activate'))
        ecomm = '. {} {} && exec {}'.format(activate, envname, cmd_string)
        ecomm = ['sh' if 'bsd' in sys.platform else 'bash', '-c', ecomm]
        os.execvp(ecomm[0], ecomm)


if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
