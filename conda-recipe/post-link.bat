@echo off
(
  "%PREFIX%\python.exe" -m nb_conda_kernels enable
) >>"%PREFIX%\.messages.txt" 2>&1
