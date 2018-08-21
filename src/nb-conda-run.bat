@echo off
rem usage: nb-conda-run <conda-root> <env> <cmd> [<arg>...]

setlocal
set conda_root=%1
shift
set envname=%1
if "%envname%" == "base" set envname="root"

rem copy the remaining arguments for the command
set cmdstring=
:loop1
shift
if [%1]==[] goto loopdone
set cmdstring=%cmdstring% %1
goto loop1
:loopdone

rem activate the requested environment and execute
call "%conda_root%\Scripts\activate" %envname%
%cmdstring%

