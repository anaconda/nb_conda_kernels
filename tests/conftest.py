import pytest

from jupyter_client.kernelspec import KernelSpecManager
from jupyter_client.manager import KernelManager

from nb_conda_kernels.manager import CondaKernelSpecManager


@pytest.fixture(scope="function")
def jupyter_manager(tmp_path):
    jupyter_data_dir = tmp_path / "share" / "jupyter"
    jupyter_data_dir.mkdir(parents=True, exist_ok=True)
    manager = CondaKernelSpecManager(kernelspec_path=str(tmp_path))
    # Install the kernel specs
    manager.find_kernel_specs()

    return KernelSpecManager(kernel_dirs=[str(jupyter_data_dir / "kernels")])


@pytest.fixture
def jupyter_kernel(jupyter_manager, request):
    return KernelManager(
        kernel_spec_manager=jupyter_manager,
        kernel_name=request.param,
    )
