$PYTHON -m pip install --no-deps --ignore-installed .

mkdir -p "$PREFIX"/bin

POST_LINK="$PREFIX"/bin/.nb_conda_kernels-post-link.sh
PRE_UNLINK="$PREFIX"/bin/.nb_conda_kernels-pre-unlink.sh

cp "$SRC_DIR"/conda-recipe/post-link.sh "$POST_LINK"
cp "$SRC_DIR"/conda-recipe/pre-unlink.sh "$PRE_UNLINK"

chmod +x "$POST_LINK" "$PRE_UNLINK"
