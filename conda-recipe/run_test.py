import os
import sys

from subprocess import call, check_output, STDOUT
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

shell = sys.platform.startswith('win')

# conda_run tests
print('Testing nb-conda-run:')
for key, value in spec_manager._all_specs().items():
    # Can't test the root prefix within conda build due to a
    # strange interaction with conda activate
    if key.startswith('conda-root-'):
        continue
    env_name = value['argv'][2]
    command = ['nb-conda-run', conda_root, env_name]
    if key.endswith('-py'):
        command.extend(['python', '-c', 'import sys; print(sys.prefix)'])
    elif key.endswith('-r'):
        command.extend(['Rscript', '--verbose', '-e', 'cat(dirname(dirname(dirname(.libPaths()))),fill=TRUE)'])
    else:
        continue
    print('  {}'.format(env_name, ' '.join(command)))
    com_out = check_output(command, shell=shell, stderr=STDOUT).decode()
    last_line = com_out.splitlines()[-1].strip()
    print('    Obtained: {}'.format(last_line))
    if last_line != env_name:
        print('FAILED; skipping further tests.')
        print('Full output:\n--------\n{}\n--------'.format(com_out))
        exit(-1)

if os.environ.get('SKIP_NPM_TESTS'):
    print('Skipping NPM tests')
    exit(0)

print('Installing NPM test packages:')
command = ['npm', 'install']
print('Calling: {}'.format(' '.join(command)))
status = call(command, shell=shell)
if status:
    exit(status)

print('Running NPM tests:')
command = ['npm', 'run', 'test']
print('Calling: {}'.format(' '.join(command)))
status = call(command, shell=shell)
if status:
    exit(status)
