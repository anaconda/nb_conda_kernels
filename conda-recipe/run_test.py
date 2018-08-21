import os
import sys

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

spec_manager = CondaKernelSpecManager()
conda_info = spec_manager._conda_info
if conda_info is None:
    print('Cannot find conda, skipping tests.')
    exit(-1)
conda_root = conda_info['root_prefix']
envs_root = conda_info['envs_dirs'][0]
print('Current prefix: {}'.format(sys.prefix))
print('Root prefix: {}'.format(conda_root))
print('Environments:')
for env in conda_info['envs']:
    print('  - {}'.format(env))
print('Kernels included in _all_specs:')
for key, value in spec_manager._all_specs().items():
    print('  - {}: {}'.format(key, value['argv'][2]))
checks = {}
print('Kernels included in get_all_specs:')
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

is_win = sys.platform.startswith('win')

# conda_run tests
any_fail = False
print('Testing nb-conda-run:')
for key, value in spec_manager._all_specs().items():
    command = value['argv'][:3]
    env_name = command[-1]
    if key.startswith('conda-root-'):
        # We can't do the same test for the root prefix because of a
        # strange interaction with conda activate. CONDA_PREFIX is
        # set properly but not PATH. I'm still investigating but it
        # does not seem to appear in testing outside of conda build.
        command.extend(['python', '-c', 'import os; print(os.environ["CONDA_PREFIX"])'])
    elif key.endswith('-py'):
        command.extend(['python', '-c', 'import sys; print(sys.prefix)'])
    elif key.endswith('-r'):
        command.extend(['Rscript', '-e', 'message(dirname(dirname(dirname(.libPaths()))))'])
        if is_win:
            env_name = env_name.replace('\\', '/')
    else:
        continue
    print('  {}'.format(' '.join(command)))
    try:
        com_out = check_output(command, shell=is_win, stderr=STDOUT).decode()
        valid = True
    except CalledProcessError as exc:
        com_out = exc.output
        valid = False
    last_line = com_out.splitlines()[-1].strip()
    print('    {}'.format(last_line))
    if not valid or last_line != env_name:
        print('Full output:\n--------\n{}\n--------'.format(com_out))
        any_fail = True
if any_fail:
    exit(-1)

if os.environ.get('SKIP_NPM_TESTS'):
    print('Skipping NPM tests')
    exit(0)

print('Installing NPM test packages:')
command = ['npm', 'install']
print('Calling: {}'.format(' '.join(command)))
status = call(command, shell=is_win)
if status:
    exit(status)

print('Running NPM tests:')
command = ['npm', 'run', 'test']
print('Calling: {}'.format(' '.join(command)))
status = call(command, shell=is_win)
if status:
    exit(status)
