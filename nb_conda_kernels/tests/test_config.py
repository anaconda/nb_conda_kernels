from __future__ import print_function

import sys
import json

from sys import prefix
from nb_conda_kernels.manager import CondaKernelSpecManager, RUNNER_COMMAND

# The testing regime for nb_conda_kernels is unique, in that it needs to
# see an entire conda installation with multiple environments and both
# Python and R kernels in those environments. In contrast, most conda
# build sessions are by design limited in context to a single environment.
# For this reason, we're doing some checks here to verify that this
# global environment is ready to receive the other tests.


old_print = print
def print(x):
    old_print('\n'.join(json.dumps(y)[1:-1] for y in x.splitlines()))
    sys.stdout.flush()


def test_configuration():
    print('\nConda configuration')
    print('-------------------')
    spec_manager = CondaKernelSpecManager()
    conda_info = spec_manager._conda_info
    if conda_info is None:
        print('ERROR: Could not find conda find conda.')
        exit(-1)
    print(u'Current prefix: {}'.format(prefix))
    print(u'Root prefix: {}'.format(conda_info['root_prefix']))
    print(u'Conda version: {}'.format(conda_info['conda_version']))
    print(u'Environments:')
    for env in conda_info['envs']:
        print(u'  - {}'.format(env))
    checks = {}
    print('Kernels included in get_all_specs')
    print('---------------------------------')
    for key, value in spec_manager.get_all_specs().items():
        if value['spec']['argv'][:3] == RUNNER_COMMAND:
            long_env = value['spec']['argv'][4]
        else:
            long_env = prefix
        print(u'  - {}: {}'.format(key, long_env))
        if key.startswith('conda-'):
            if long_env == prefix:
                checks['env_current'] = True
            if key.startswith('conda-root-'):
                checks['root_py'] = True
            if key.startswith('conda-env-'):
                if len(key.split('-')) >= 5:
                    checks['env_project'] = True
                if key.endswith('-py'):
                    checks['env_py'] = True
                if key.endswith('-r'):
                    checks['env_r'] = True
            try:
                long_env.encode('ascii')
            except UnicodeEncodeError:
                checks['env_unicode'] = True
        elif key.lower().startswith('python'):
            checks['default_py'] = True
    print('Scenarios required for proper testing')
    print('-------------------------------------')
    print('  - Python kernel in test environment: {}'.format(bool(checks.get('default_py'))))
    print('  - ... included in the conda kernel list: {}'.format(bool(checks.get('env_current'))))
    print('  - Python kernel in root environment: {}'.format(bool(checks.get('root_py'))))
    print('  - Python kernel in other environment: {}'.format(bool(checks.get('env_py'))))
    print('  - R kernel in non-test environment: {}'.format(bool(checks.get('env_r'))))
    print('  - Environment with non-ASCII name: {}'.format(bool(checks.get('env_unicode'))))
    print('  - External project environment: {}'.format(bool(checks.get('env_project'))))
    # In some conda build scenarios, the test environment is not returned by conda
    # in the listing of conda environments.
    if 'conda-bld' in prefix:
        checks.setdefault('env_current', False)
    # It is difficult to get AppVeyor to handle Unicode environments well, but manual testing
    # on Windows works fine. So it is likely related to the way AppVeyor captures output
    if sys.platform.startswith('win'):
        checks.setdefault('env_unicode', False)
    assert len(checks) >= 7


if __name__ == '__main__':
    test_configuration()
