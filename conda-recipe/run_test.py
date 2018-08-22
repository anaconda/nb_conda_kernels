import os
import sys
import site

from subprocess import call, check_output, STDOUT, CalledProcessError
from nb_conda_kernels import CondaKernelSpecManager

# The testing regime for nb_conda_kernels is unique, in that it needs to
# see an entire conda installation with multiple environments and both
# Python and R kernels in those environments. In contrast, most conda
# build sessions are by design limited in context to a single environment.
# For this reason, we're doing some checks here to verify that this
# global environment is what the subsequent npm-based tests expect
# to see before launching the full npm session. This was a lot easier
# to accomplish with a Python-based conda build test script.

print('')
print('Conda configuration')
print('-------------------')
spec_manager = CondaKernelSpecManager()
conda_info = spec_manager._conda_info
if conda_info is None:
    print('ERROR: Could not find conda find conda.')
    exit(-1)
print('Current prefix: {}'.format(sys.prefix))
print('Root prefix: {}'.format(conda_info['root_prefix']))
print('Conda version: {}'.format(conda_info['conda_version']))
print('Environments:')
for env in conda_info['envs']:
    print('  - {}'.format(env))

checks = {}
print('')
print('Kernels included in get_all_specs')
print('---------------------------------')
for key, value in spec_manager.get_all_specs().items():
    long_env = value['spec']['argv'][2] if key.startswith('conda-') else sys.prefix
    print('  - {}: {}'.format(key, long_env))
    key = key.lower()
    if key.startswith('python'):
        checks['default_py'] = True
    if key.startswith('ir'):
        checks['default_r'] = True
    if key.startswith('conda-root-py'):
        checks['root_py'] = True
    if key.startswith('conda-env-'):
        if key.endswith('-py'):
            checks['env_py'] = True
        if key.endswith('-r'):
            checks['env_r'] = True
if len(checks) < 5:
    print('ERROR: the environment is not properly configured for testing:')
    if not checks.get('default_py'):
        print('  - Default Python kernel missing')
    if not checks.get('default_r'):
        print('  - Default R kernel missing')
    if not checks.get('root_py'):
        print('  - Root Python kernel missing')
    if not checks.get('env_py'):
        print('  - Environment Python kernel missing')
    if not checks.get('env_r'):
        print('  - Environment R kernel missing')
    print('Skipping further tests.')
    exit(-1)

# Due to a bug in conda build, activating other conda
# environments during a conda build test session fails
# under certain circumstances. The symptom is that the PATH
# is not set properly, but CONDA_PREFIX is. The issue
# is isolated to conda build itself; that is, we do not
# see this behavior during normal operation. For now, we
# have weakened this test somewhat: CONDA_PREFIX must
# always be correct, but we need to see only a single
# correct PATH value.

is_win = sys.platform.startswith('win')
strong_fail = 0
weak_pass = 0
print('')
print('Tests for nb-conda-run')
print('----------------------')
for key, value in spec_manager._all_specs().items():
    command = value['argv'][:3]
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
    valid = True
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
if strong_fail != 0 or weak_pass == 0:
    exit(-1)

