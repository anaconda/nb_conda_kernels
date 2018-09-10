import os
import sys

from nb_conda_kernels.discovery import CondaKernelProvider

is_win = sys.platform.startswith('win')
is_py2 = sys.version_info[0] < 3


provider = CondaKernelProvider()


def check_exec_in_env(key):
    kernel_manager = provider.make_manager(key)
    env_name = kernel_manager.kernel_spec.argv[4]
    env_name_fs = env_name.replace('\\', '/')
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
                        'cat(dirname(dirname(dirname(.libPaths()))),fill=TRUE)']
        else:
            commands = ['import os, sys',
                        'print(os.environ["CONDA_PREFIX"])',
                        'print(sys.prefix)']
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
            kernel_manager.finish_shutdown(waittime=5)
    print(u'{}: {}\n--------\n{}\n--------'.format(key, env_name, '\n'.join(outputs)))
    assert valid and len(outputs) >= 2 and all(o in (env_name, env_name_fs) for o in outputs[-2:])


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
