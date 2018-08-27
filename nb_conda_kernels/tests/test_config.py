from sys import prefix
from nb_conda_kernels.manager import CondaKernelSpecManager

# The testing regime for nb_conda_kernels is unique, in that it needs to
# see an entire conda installation with multiple environments and both
# Python and R kernels in those environments. In contrast, most conda
# build sessions are by design limited in context to a single environment.
# For this reason, we're doing some checks here to verify that this
# global environment is ready to receive the other tests.


def test_configuration():
    print('Conda configuration')
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
        long_env = value['spec']['argv'][4] if key.startswith('conda-') else prefix
        print(u'  - {}: {}'.format(key, long_env))
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
        print('The environment is not properly configured for testing:')
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
        assert False


if __name__ == '__main__':
    test_configuration()

