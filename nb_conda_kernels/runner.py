from __future__ import print_function

import re
import os
import sys
import locale

from subprocess import check_output, Popen

is_py2 = sys.version_info.major < 3
is_win = sys.platform.startswith('win')


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
        ecomm = 'chcp 65001 & call "{}" "{}">nul & set'.format(activate, envname)
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
    env = check_output(ecomm, shell=is_win).decode(encoding)
    env = env.splitlines()

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
    if is_py2:
        if is_win:
            fullpath = fullpath.encode(encoding)
        env = {k.encode(encoding): v.encode(encoding)
               for k, v in env.items()}

    # Launch the kernel process
    if is_win:
        # Methodology: create a job object to hold the subprocess so
        # all of its children will be killed when it completes.
        # https://stackoverflow.com/a/23587108
        import win32api, win32con, win32job  # noqa
        hJob = win32job.CreateJobObject(None, "")
        extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
        extended_info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)
        perms = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA
        child = Popen((fullpath,) + args, env=env)
        hProcess = win32api.OpenProcess(perms, False, child.pid)
        win32job.AssignProcessToJobObject(hJob, hProcess)
        child.wait()
    else:
        os.execvpe(command, (command,) + args, env)


if __name__ == '__main__':
    exec_in_env(*(sys.argv[1:]))
