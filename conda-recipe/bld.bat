%PYTHON% -m pip install --no-deps --ignore-installed .
if errorlevel 1 exit 1

set SCRIPTS="%PREFIX%\Scripts"
if not exist %SCRIPTS% mkdir %SCRIPTS%
if errorlevel 1 exit 1

copy %SRC_DIR%\conda-recipe\post-link.bat %SCRIPTS%\.nb_conda_kernels-post-link.bat || exit 1
copy %SRC_DIR%\conda-recipe\pre-unlink.bat %SCRIPTS%\.nb_conda_kernels-pre-unlink.bat || exit 1
