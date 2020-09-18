from __future__ import print_function

import io
import locale
import os
import sys
import json
import tempfile
import time
import pytest

from nb_conda_kernels.discovery import CondaKernelProvider
from nb_conda_kernels.manager import RUNNER_COMMAND
from jupyter_client.blocking.client import Empty

START_TIMEOUT = 10
CMD_TIMEOUT = 3
NUM_RETRIES = 10
is_win = sys.platform.startswith('win')
is_py2 = sys.version_info[0] < 3


provider = CondaKernelProvider()


old_print = print
def print(x):
    old_print('\n'.join(json.dumps(y)[1:-1] for y in x.splitlines()))
    sys.stdout.flush()


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


def find_test_keys():
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
    keys = []
    for key, _ in provider.find_kernels():
        assert key.startswith('conda-')
        if key.endswith('-py') or key.endswith('-r'):
            keys.append(key)
    return keys


def call_kernel(kernel_manager, **kw):
    name = kernel_manager.kernel_name

    valid = False
    # For reasons we do not fully understand, the kernels sometimes die immediately
    # and sometimes hang in this loop. Frankly the purpose of this test is not to
    # understand why that is but to simply test that a successfully run kernel is
    # using the correct environment. So we're using a simple retry loop, and we
    # use a timeout when waiting for messages from the kernel.
    for tries in range(NUM_RETRIES):
        outputs = []
        client = None
        try:
            print('\n--- attempt {}'.format(tries+1))
            kernel_manager.start_kernel(**kw)
            client = kernel_manager.client()
            client.start_channels()
            client.wait_for_ready(timeout=START_TIMEOUT)
            if name.endswith('-r'):
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
                while True:
                    msg = client.get_iopub_msg(timeout=CMD_TIMEOUT)['content']
                    if msg.get('execution_state') == 'idle':
                        break
                    if msg.get('name') == 'stdout':
                        outputs.append(msg['text'].strip())
                        print(outputs[-1])
            valid = True
        except:
            time.sleep(CMD_TIMEOUT)
            pass
        finally:
            if client is not None:
                client.stop_channels()
            if kernel_manager.is_alive():
                kernel_manager.request_shutdown()
                kernel_manager.finish_shutdown()
        if valid:
            break
    else:
        assert False, 'Did not successfully run kernel'

    return valid, outputs


@pytest.mark.parametrize("key", find_test_keys())
def test_runner(key):
    kernel_manager = provider.make_manager(key)
    if kernel_manager.kernel_spec.argv[:3] == RUNNER_COMMAND:
        env_path = kernel_manager.kernel_spec.argv[4]
    else:
        env_path = sys.prefix
    env_path = os.path.normcase(os.path.normpath(env_path))

    valid, outputs = call_kernel(kernel_manager)

    assert valid and len(outputs) >= 2
    for o in outputs[-2:]:
        assert os.path.normcase(os.path.normpath(o)) == env_path, (o, env_path)


@pytest.mark.parametrize("jupyter_kernel", find_test_keys(), indirect=True)
def test_jupyter_kernelspecs_runner(tmp_path, jupyter_kernel):
    if sys.platform.startswith("linux") and jupyter_kernel.kernel_name == "conda-env-t_st_env2-py":
        pytest.xfail("Folder with unicode raises error on linux.")

    fake_stdout = tmp_path / "stdout.log"
    # RUNNER_COMMAND is installed in all exported kernelspec
    assert jupyter_kernel.kernel_spec.argv[:3] == RUNNER_COMMAND

    env_path = jupyter_kernel.kernel_spec.argv[4]
    env_path = os.path.normcase(os.path.normpath(env_path))

    with fake_stdout.open("wb") as t:  # Catch the echo set in the runner
        valid, outputs = call_kernel(jupyter_kernel, stdout=t)

    assert valid and len(outputs) >= 2
    for o in outputs[-2:]:
        assert os.path.normcase(os.path.normpath(o)) == env_path, (o, env_path)

    # The nb_conda_kernels.runner skip activation if sys.prefix is the active environment
    # Don't know why but character from the echo command are separated
    # with a null character on Windows
    captured_stdout = fake_stdout.read_text().replace("\00", "")
    assert ("CONDA_PREFIX=" in captured_stdout) == (env_path.lower() != sys.prefix.lower())


if __name__ == '__main__':
    for key in find_test_keys():
        test_runner(key)
