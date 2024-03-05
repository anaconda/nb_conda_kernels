%PYTHON% -m pip install --no-deps --ignore-installed .
if errorlevel 1 exit 1

set SCRDIR="%PREFIX%\Scripts"
if not exist %SCRDIR% mkdir %SCRDIR%
if errorlevel 1 exit 1

POST_LINK="%SCRDIR%\.nb_conda_kernels-post-link"
PRE_UNLINK="%SCRDIR%\.nb_conda_kernels-pre-unlink"

copy "%SRC_DIR%\conda-recipe\post-link.bat" "%POST_LINK%.bat" || exit 1
copy "%SRC_DIR%\conda-recipe\pre-unlink.bat" "%PRE_UNLINK%.bat" || exit 1
copy "%SRC_DIR%\conda-recipe\post-link.sh" "%POST_LINK%.sh" || exit 1
copy "%SRC_DIR%\conda-recipe\pre-unlink.sh" "%PRE_UNLINK%.sh" || exit 1
