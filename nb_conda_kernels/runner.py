from __future__ import print_function

import os
import sys
import subprocess
import locale
try:
    from shlex import quote
except ImportError:
    from pipes import quote


def exec_in_env(conda_root, envname, *command):
    # Run the standard conda activation script, and print the
    # resulting environment variables to stdout for reading.
    if sys.platform.startswith('win'):
        print(sys.stdin.encoding, sys.stdout.encoding, sys.stderr.encoding, locale.getpreferredencoding())
        activate = os.path.join(conda_root, 'Scripts', 'activate.bat')
        activator = subprocess.list2cmdline(['call', activate, envname])
        ecomm = [os.environ['COMSPEC'], '/S', '/U', '/C', '@echo', 'off', '&&',
                 'chcp', '&&', 'call', 'activate', envname, '&&'] + list(command)
        subprocess.Popen(ecomm).wait()
    else:
        command = ' '.join(quote(c) for c in command)
        activate = os.path.join(conda_root, 'bin', 'activate')
        ecomm = ". '{}' '{}' && exec {}".format(activate, envname, command)
        ecomm = ['sh' if 'bsd' in sys.platform else 'bash', '-c', ecomm]
        os.execvp(ecomm[0], ecomm)


if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
