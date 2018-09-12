# Initial support for the kernel provider mechanism
# to be introduced in jupyter_client 6.0; see
# https://jupyter-client.readthedocs.io/en/latest/kernel_providers.html

try:
    from jupyter_client.discovery import KernelProviderBase
except ImportError:
    # Silently fail for version of jupyter_client that do not
    # yet have the discovery module. This allows us to do some
    # simple testing of this code even with jupyter_client<6
    KernelProviderBase = object

from jupyter_client.manager import KernelManager
from .manager import CondaKernelSpecManager


class CondaKernelProvider(KernelProviderBase):
    id = 'conda'

    def __init__(self):
        self.cksm = CondaKernelSpecManager(conda_only=True)

    def find_kernels(self):
        for name, data in self.cksm.get_all_specs().items():
            yield name, data['spec']

    def make_manager(self, name):
        return KernelManager(kernel_spec_manager=self.cksm, kernel_name=name)
