from __future__ import print_function

import json
import os
import sys
from sys import prefix

try:
    from unittest.mock import call, patch
except ImportError:
    from mock import call, patch  # py2

import pytest
from traitlets.config import Config, TraitError
from nb_conda_kernels.manager import RUNNER_COMMAND, CondaKernelSpecManager

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
            assert long_env == value['spec']['metadata']['conda_env_path']
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


@pytest.mark.parametrize("kernelspec_path, user, prefix, expected", [
    (
        "",
        False, "", ""),  # Usually it is not allowed to write at system level
    (
        "--user",
        True, None, "--user"),
    (
        "--sys-prefix",
        False, sys.prefix, "--sys-prefix"),
    (
        os.path.dirname(__file__),
        False, os.path.dirname(__file__), os.path.dirname(__file__)),
    (
        "/dummy/path",
        False, None, TraitError),
    (
        __file__,
        False, None, TraitError),
])
def test_kernelspec_path(tmp_path, kernelspec_path, user, prefix, expected):
    config = Config({"CondaKernelSpecManager": {"kernelspec_path": kernelspec_path}})
    with patch("nb_conda_kernels.manager.CondaKernelSpecManager.install_kernel_spec") as install:
        install.return_value = str(tmp_path)        
        if isinstance(expected, type) and issubclass(expected, Exception):
            with pytest.raises(expected):
                CondaKernelSpecManager(config=config)
        else:
            spec_manager = CondaKernelSpecManager(config=config)
            assert spec_manager.kernelspec_path == expected
            assert spec_manager.conda_only == (spec_manager.kernelspec_path is not None)
            for call_ in install.call_args_list:
                assert call_[1]["user"] == user
                assert call_[1]["prefix"] ==prefix


@pytest.mark.parametrize("kernelspec_path", ["", None])
def test_install_kernelspec(tmp_path, kernelspec_path):
    config = Config({"CondaKernelSpecManager": {"kernelspec_path": kernelspec_path}})
    with patch("nb_conda_kernels.manager.CondaKernelSpecManager.install_kernel_spec") as install:
        install.return_value = str(tmp_path)
        CondaKernelSpecManager(config=config)
        
        assert install.called == (kernelspec_path is not None)

@pytest.mark.parametrize("kernel_name, expected", [
    ("not-conda-kernel", False),
    ("conda-env-dummy-cpp", True)
])
def test_remove_kernelspec(tmp_path, kernel_name, expected):
    config = Config({"CondaKernelSpecManager": {"kernelspec_path": ""}})
    kernel_spec = tmp_path / kernel_name / "kernel.json"
    kernel_spec.parent.mkdir()
    kernel_spec.write_bytes(b"{}")
    with patch("nb_conda_kernels.manager.CondaKernelSpecManager.install_kernel_spec") as install:
        install.return_value = str(tmp_path)
        with patch("nb_conda_kernels.manager.CondaKernelSpecManager._get_destination_dir") as destination:
            destination.return_value = str(tmp_path)
            with patch("shutil.rmtree") as remove:
                CondaKernelSpecManager(config=config)
                
                assert remove.called == expected


@pytest.mark.parametrize("kernelspec", [
    {
        "display_name": "xpython",
        "argv": [
            "@XPYTHON_KERNELSPEC_PATH@xpython",
            "-f",
            "{connection_file}"
        ],
        "language": "python",
        "metadata": { "debugger": True }
    }
])
def test_kernel_metadata(monkeypatch, tmp_path, kernelspec):

    mock_info = {
        'conda_prefix': '/'
    }

    def envs(*args):
        return {
            'env_name': str(tmp_path)
        }

    kernel_file = tmp_path / 'share' / 'jupyter' / 'kernels' / 'my_kernel' / 'kernel.json'
    kernel_file.parent.mkdir(parents=True, exist_ok=True)
    if sys.version_info >= (3, 0):
        kernel_file.write_text(json.dumps(kernelspec))
    else:
        kernel_file.write_bytes(json.dumps(kernelspec))

    monkeypatch.setattr(CondaKernelSpecManager, "_conda_info", mock_info)
    monkeypatch.setattr(CondaKernelSpecManager, "_all_envs", envs)

    manager = CondaKernelSpecManager()
    specs = manager._all_specs()

    assert len(specs) == 1
    for spec in specs.values():
        metadata = spec['metadata']
        for key, value in kernelspec['metadata'].items():
            assert key in metadata
            assert metadata[key] == value


if __name__ == '__main__':
    test_configuration()
