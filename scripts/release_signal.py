import os
from subprocess import CalledProcessError, check_output

try:
    check_output('git describe --exact-match HEAD'.split())
    print("We are in a tagged branch, let's do the release")
except CalledProcessError as e:
    print("We are not in a tagged branch")
else:
    os.environ["ANE_RELEASE"] = "1"
