import re
import os
import sys

from subprocess import check_output, Popen

def exec_in_env(conda_root, envname, command, *args):
    # Run the standard conda activation script, and print the
    # resulting environment variables to stdout for reading.
    is_win = sys.platform.startswith('win')
    if is_win:
        activate = os.path.join(conda_root, 'Scripts', 'activate.bat')
        ecomm = 'call "{}" "{}">nul & set'.format(activate, envname)
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
        ecomm = '. "{}" "{}" >/dev/null && printenv'.format(activate, envname)
        ecomm = ['bash', '-c', ecomm]
    env = check_output(ecomm, shell=is_win)
    encoding = sys.stdout.encoding or 'utf-8'
    env = env.decode(encoding).splitlines()
    # print(type(env[-1]), type('='), type('@@@'))

    # Extract the path search results (Windows only). The "where"
    # command behaves like "which -a" in Unix, listing *all*
    # locations in the PATH where the executable can be found.
    # We need just the first.
    if is_win and not fullpath:
        while not env[-1].startswith(u'@@@'):
            fullpath = env.pop()
        env.pop()
        if not fullpath:
            raise RuntimeError('Could not find full path for executable {}'.format(command))

    # Extract the environment variables from the output, so we can
    # pass them to the kernel process.
    env = dict(p.split(u'=', 1) for p in env if u'=' in p)
    # Python 2 does not support unicode env dicts
    if sys.version_info.major < 3:
        env = {k.encode(encoding): v.encode(encoding)
               for k, v in env.items()}

    # Launch the kernel process
    if is_win:
        Popen((fullpath,) + args, env=env).wait()
    else:
        os.execvpe(command, (command,) + args, env)


if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
