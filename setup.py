import setuptools
import versioneer

setuptools.setup(
    name="nb_conda_kernels",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    url="https://github.com/Anaconda-Platform/nb_conda_kernels",
    author="Continuum Analytics",
    description="Launch Jupyter kernels for any installed conda environment",
    long_description=open('README.md').read(),
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False
)
