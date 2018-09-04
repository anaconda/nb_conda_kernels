@echo off
(
  "%PREFIX%\python.exe" -m nb_conda_kernels.install --enable
) >>"%PREFIX%\.messages.txt" 2>&1
