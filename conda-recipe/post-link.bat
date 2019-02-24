@echo off
:: Set PATH explicitly as it may not be set correctly by some versions of conda
set "PATH=%PATH%;%PREFIX%\Library\bin"
"%PREFIX%\python.exe" -m nb_conda_kernels.install --enable >>"%PREFIX%\.messages.txt" 2>&1 && if errorlevel 1 exit 1
