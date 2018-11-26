import os
import sys

from nb_conda_kernels.discovery import CondaKernelProvider
from nb_conda_kernels.manager import RUNNER_COMMAND

is_win = sys.platform.startswith('win')
is_py2 = sys.version_info[0] < 3


provider = CondaKernelProvider()

if is_win:
    # Create a job object and assign ourselves to it, so that
    # all remaining test subprocesses get killed off on completion.
    # This prevents AppVeyor from waiting an hour
    # https://stackoverflow.com/a/23587108 (and its first comment)
    import win32api, win32con, win32job  # noqa
    hJob = win32job.CreateJobObject(None, "")
    extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
    extended_info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)
    perms = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA
    hProcess = win32api.OpenProcess(perms, False, os.getpid())
    win32job.AssignProcessToJobObject(hJob, hProcess)


def check_exec_in_env(key):
    kernel_manager = provider.make_manager(key)
    if kernel_manager.kernel_spec.argv[:3] == RUNNER_COMMAND:
        env_path = kernel_manager.kernel_spec.argv[4]
    else:
        env_path = sys.prefix
    env_path_fs = env_path.replace('\\', '/')
    client = None
    valid = False
    outputs = []
    try:
        print('Starting kernel: {}'.format(key))
        kernel_manager.start_kernel()
        print('Initializing client')
        client = kernel_manager.client()
        client.start_channels()
        client.wait_for_ready(timeout=60)
        if key.endswith('-r'):
            commands = ['cat(Sys.getenv("CONDA_PREFIX"),fill=TRUE)',
                        'cat(dirname(dirname(dirname(.libPaths()))),fill=TRUE)',
                        'quit(save="no")']
        else:
            commands = ['import os, sys',
                        'print(os.environ["CONDA_PREFIX"])',
                        'print(sys.prefix)',
                        'quit']
        for command in commands:
            print('>>> {}'.format(command))
            m_id = client.execute(command)
            client.get_shell_msg(m_id)
            while True:
                msg = client.get_iopub_msg()['content']
                if msg.get('execution_state') == 'idle':
                    break
                if msg.get('name') == 'stdout':
                    outputs.append(msg['text'].strip())
                    print(outputs[-1])
        valid = True
    finally:
        if client is None:
            print('Cleaning up client')
            client.stop_channels()
        if kernel_manager.is_alive():
            print('Requesting shutdown')
            kernel_manager.request_shutdown()
    print(u'{}: {}\n--------\n{}\n--------'.format(key, env_path, '\n'.join(outputs)))
    assert valid and len(outputs) >= 2 and all(o in (env_path, env_path_fs) for o in outputs[-2:])


def test_runner():
    if os.environ.get('CONDA_BUILD'):
        # The current version of conda build manually adds the activation
        # directories to the PATH---and then calls the standard conda
        # activation script, which does it again. This frustrates conda's
        # ability to deactivate this environment. Most package builds are
        # not affected by this, but we are, because our tests need to do
        # environment activation and deactivation. To fix this, we remove
        # the duplicate PATH entries conda-build added.
        print('BEFORE: {}'.format(os.environ['PATH']))
        path_list = os.environ['PATH'].split(os.pathsep)
        path_dups = set()
        path_list = [p for p in path_list
                     if not p.startswith(sys.prefix) or
                     p not in path_dups and not path_dups.add(p)]
        os.environ['PATH'] = os.pathsep.join(path_list)
        print('AFTER: {}'.format(os.environ['PATH']))
    for key, _ in provider.find_kernels():
        assert key.startswith('conda-')
        if key.endswith('-py') or key.endswith('-r'):
            yield check_exec_in_env, key


if __name__ == '__main__':
    for func, key in test_runner():
        func(key)
