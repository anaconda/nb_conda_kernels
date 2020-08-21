from jupyter_client import kernelspec
from .manager import CondaKernelSpecManager
kernelspec.KernelSpecManager = CondaKernelSpecManager

from jupyter_client.kernelspecapp import KernelSpecApp  # noqa

KernelSpecApp.launch_instance()
