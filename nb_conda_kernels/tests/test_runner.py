import os
import sys
import locale

from subprocess import check_output, CalledProcessError, STDOUT
from nb_conda_kernels.manager import CondaKernelSpecManager

is_win = sys.platform.startswith('win')
is_py2 = sys.version_info[0] < 3

def check_exec_in_env(key, argv):
    command = argv[:5]
    env_name = command[-1]
    env_name_fs = env_name.replace('\\', '/')
    if key.endswith('-r'):
        command.extend(['Rscript', '-e',
                        'cat(Sys.getenv("CONDA_PREFIX"),fill=TRUE);'
                        'cat(dirname(dirname(dirname(.libPaths()))),fill=TRUE)'])
    else:
        command.extend(['python', '-c',
                        'import os,sys;'
                        'print(os.environ["CONDA_PREFIX"]);'
                        'print(sys.prefix)'])
    encoding = locale.getpreferredencoding(False)
    if 'ascii' in encoding.lower():
        encoding = 'utf-8'
    if is_py2:
        command = [c.encode(encoding) for c in command]
    try:
        com_out = check_output(command)
        valid = True
    except CalledProcessError as exc:
        com_out = exc.output
        valid = False
    com_out = com_out.decode(encoding)
    outputs = com_out.splitlines()
    if not (valid and len(outputs) >= 2 and
            all(o.strip() in (env_name, env_name_fs) for o in outputs[-2:])):
        print(u'Full output:\n--------\n{}--------'.format(com_out))
        assert False


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
    spec_manager = CondaKernelSpecManager()
    for key, value in spec_manager._all_specs().items():
        if key.endswith('-py') or key.endswith('-r'):
            yield check_exec_in_env, key, value['argv']


if __name__ == '__main__':
    for func, key, val in test_runner():
        print(u'{}: {}'.format(key, u' '.join(val[:5])))
        print('--------')
        func(key, val)
