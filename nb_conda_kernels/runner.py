from __future__ import print_function

import re
import os
import sys
import json
import locale

from subprocess import check_output, Popen

is_py2 = sys.version_info.major < 3
is_win = sys.platform.startswith('win')
env_cmd = '{} -c "import os,json;print(json.dumps(dict(os.environ)))"'.format(sys.executable)


def exec_in_env(conda_root, envname, command, *args):
    # Run the standard conda activation script, and print the
    # resulting environment variables to stdout for reading.
    encoding = locale.getpreferredencoding()
    if 'ascii' in encoding.lower():
        encoding = 'utf-8'

    if is_win:
        activate = os.path.join(conda_root, 'Scripts', 'activate.bat')
        # For some reason I need to set the code page to utf-8
        # in order to get output that I can later decode using
        # the default encoding (typically 1252/latin-1) downstream
        ecomm = 'chcp 65001 & call "{}" "{}">nul & {}'.format(activate, envname, env_cmd)
        if os.sep in command:
            fullpath = command
        else:
            # For Windows, we also need to obtain the full path to
            # the target executable.
            ecomm += ' & echo @@@ & where $path:{}'.format(command)
            fullpath = None
    else:
        activate = os.path.join(conda_root, 'bin', 'activate')
        activate = re.sub(r'([$"\\])', '\\\g<1>', activate)
        envname = re.sub(r'([$"\\])', '\\\g<1>', envname)
        ecomm = '. "{}" "{}" >/dev/null && {}'.format(activate, envname, env_cmd)
        ecomm = ['bash', '-c', ecomm]
    env = check_output(ecomm, shell=is_win).decode(encoding)

    # Extract the path search results (Windows only). The "where"
    # command behaves like "which -a" in Unix, listing *all*
    # locations in the PATH where the executable can be found.
    # We need just the first.
    if is_win and not fullpath:
        parts = env.rsplit('@@@\n', 1)
        if len(parts) != 2 or not parts[1].strip():
            raise RuntimeError('Could not find full path for executable {}'.format(command))
        fullpath = paths.splitlines()[0]
        env = parts[0]

    # Extract the environment variables from the output, so we can
    # pass them to the kernel process.
    env = json.loads(env)
    # Python 2 does not support unicode env dicts
    if is_py2:
        if is_win:
            fullpath = fullpath.encode(encoding)
        env = {k.encode(encoding): v.encode(encoding)
               for k, v in env.items()}

    # Launch the kernel process
    if is_win:
        Popen((fullpath,) + args, env=env).wait()
    else:
        os.execvpe(command, (command,) + args, env)


if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
