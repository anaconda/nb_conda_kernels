from sys import platform
from subprocess import check_output, CalledProcessError, STDOUT
from nb_conda_kernels.manager import CondaKernelSpecManager

# Due to a bug in conda build, activating other conda
# environments during a conda build test session fails
# under certain circumstances. The symptom is that the PATH
# is not set properly, but CONDA_PREFIX is. The issue
# is isolated to conda build itself; that is, we do not
# see this behavior during normal operation. For now, we
# have weakened this test somewhat: CONDA_PREFIX must
# always be correct, but we need to see only a single
# correct PATH value.

def test_runner():
    spec_manager = CondaKernelSpecManager()
    is_win = platform.startswith('win')
    strong_fail = 0
    weak_pass = 0
    for key, value in spec_manager._all_specs().items():
        command = value['argv'][:5]
        env_name = command[-1]
        if key.endswith('-py'):
            command.extend(['python', '-c',
                            'import os,sys;'
                            'print(os.environ["CONDA_PREFIX"]);'
                            'print(sys.prefix)'])
        elif key.endswith('-r'):
            command.extend(['Rscript', '-e',
                            'message(Sys.getenv("CONDA_PREFIX"));'
                            'message(dirname(dirname(dirname(.libPaths()))))'])
        else:
            continue
        command_print = command[:-1] + ["'" + command[-1] + "'"]
        print('  {}'.format(' '.join(command_print)))
        try:
            com_out = check_output(command, shell=is_win, stderr=STDOUT)
        except CalledProcessError as exc:
            com_out = exc.output
            valid = False
        com_out = com_out.decode()
        outputs = list(map(lambda x: x.strip(), com_out.splitlines()[-2:]))
        if valid and len(outputs) != 2:
            valid = False
        if valid:
            print('   CONDA_PREFIX: {}'.format(outputs[0]))
            print('     sys.prefix: {}'.format(outputs[1]))
            if outputs[0] != env_name:
                valid = False
            if outputs[1] in (env_name, env_name.replace('\\', '/')):
                weak_pass += 1
        if not valid:
            print('Full output:\n--------\n{}--------'.format(com_out))
            strong_fail += 1
    assert strong_fail == 0, "One or more CONDA_PREFIX values was incorrect"
    assert weak_pass != 0, "None of the sys.prefix values was correct"

