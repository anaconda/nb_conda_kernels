import os
import sys
import shlex
from subprocess import check_output, Popen

def exec_in_env(conda_root, envname, command, *args):
    is_win = sys.platform.startswith('win')
    if is_win:
        activate = os.path.join(conda_root, 'Scripts', 'activate.bat')
        ecomm = 'call {} {}>nul & set & where {}'.format(activate, envname, command)
    else:
        activate = os.path.join(conda_root, 'bin', 'activate')
        ecomm = '. {} {} >/dev/null && printenv'.format(activate, envname, command)
        ecomm = ['bash', '-c', ecomm]
    env = check_output(ecomm, shell=is_win).decode().splitlines()
    fullpath = env.pop() if is_win else command
    env = dict(p.split('=', 1) for p in env if '=' in p)
    if is_win:
        Popen((fullpath,) + args, env=env).wait()
    else:
        os.execvpe(fullpath, (command,) + args, env)

if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
