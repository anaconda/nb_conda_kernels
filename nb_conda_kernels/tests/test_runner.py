import os
import sys

from subprocess import check_output, CalledProcessError, STDOUT
from nb_conda_kernels.manager import CondaKernelSpecManager

is_win = sys.platform.startswith('win')


def check_exec_in_env(key, argv):
    command = argv[:5]
    env_name = command[-1]
    env_name_fs = env_name.replace('\\', '/')
    if key.endswith('-r'):
        command.extend(['Rscript', '-e',
                        'message(Sys.getenv("CONDA_PREFIX"));'
                        'message(dirname(dirname(dirname(.libPaths()))))'])
    else:
        command.extend(['python', '-c',
                        'import os,sys;'
                        'print(os.environ["CONDA_PREFIX"]);'
                        'print(sys.prefix)'])
    try:
        com_out = check_output(command, shell=is_win, stderr=STDOUT)
        valid = True
    except CalledProcessError as exc:
        com_out = exc.output
        valid = False
    outputs = com_out.decode().splitlines()
    if not (valid and len(outputs) >= 2 and
            all(o.strip() in (env_name, env_name_fs) for o in outputs[-2:])):
        print('Full output:\n--------\n{}--------'.format('\n'.join(outputs)))
        assert False


def test_runner():
    if os.environ.get('CONDA_BUILD'):
        # Current versions of conda build invoke standard conda activation
        # *and* manually add the activation paths a second time. Unfortunately,
        # this frustrate's conda's ability to activate. This backs out the
        # redundancy so that the test can proceed.
        path_list = os.environ['PATH'].split(os.pathsep)
        first_path = sys.prefix if is_win else os.path.join(sys.prefix, 'bin')
        indexes = [i for i, v in enumerate(path_list) if v == first_path]
        if len(indexes) > 1:
            path_list = path_list[indexes[-1]:]
            os.environ['PATH'] = os.pathsep.join(path_list)
    spec_manager = CondaKernelSpecManager()
    for key, value in spec_manager._all_specs().items():
        if key.endswith('-py') or key.endswith('-r'):
            yield check_exec_in_env, key, value['argv']


