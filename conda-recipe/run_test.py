import os
import sys
import json
from subprocess import call
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
print('Current prefix: {}'.format(sys.prefix))
print('Root prefix: {}'.format(conda_info['root_prefix']))
print('Environments:')
for env in conda_info['envs']:
	print('  - {}'.format(env))
print('Kernels included in _all_envs:')
for key, value in spec_manager._all_envs().items():
	print('  - {}: {}'.format(key, value['executable']))
checks = {}
print('Kernels included in get_all_specs:')
for key, value in spec_manager.get_all_specs().items():
	print('  - {}: {}'.format(key, value['spec']['argv'][0]))
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
	print('Skipping NPM tests, since they will fail.')
	exit(-1)

npm_cmd = ['npm']
if sys.platform.startswith('win'):
	npm_cmd = ['cmd.exe', '/c'] + npm_cmd

print('Installing NPM test packages:')
command = npm_cmd + ['install']
print('Calling: {}'.format(' '.join(command)))
status = call(command)
if status:
	exit(status)

print('Running NPM tests:')
command = npm_cmd + ['run', 'test']
print('Calling: {}'.format(' '.join(command)))
status = call(command)
if status:
	exit(status)
