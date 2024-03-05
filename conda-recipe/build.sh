$PYTHON -m pip install --no-deps --ignore-installed .

BINDIR="$PREFIX/bin"
mkdir -p "$BINDIR"

POST_LINK="$BINDIR/.nb_conda_kernels-post-link"
PRE_UNLINK="$BINDIR/.nb_conda_kernels-pre-unlink"

cp "$SRC_DIR/conda-recipe/post-link.sh" "$POST_LINK.sh"
cp "$SRC_DIR/conda-recipe/pre-unlink.sh" "$PRE_UNLINK.sh"
cp "$SRC_DIR/conda-recipe/post-link.bat" "$POST_LINK.bat"
cp "$SRC_DIR/conda-recipe/pre-unlink.bat" "$PRE_UNLINK.bat"
