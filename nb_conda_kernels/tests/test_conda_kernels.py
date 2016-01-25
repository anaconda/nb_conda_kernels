import json
import requests
import subprocess
import time

from os.path import split

def test_kernel_specs():

    p = subprocess.check_output(["conda", "info", "--json"]).decode("utf-8")
    conda_info = json.loads(p)
    envs = [split(base)[1] for base in conda_info["envs"]]
    envs.append("Root")
    python_envs = ["Python [{}]".format(env) for env in envs]
    r_envs = ["R [{}]".format(env) for env in envs]

    nb = subprocess.Popen(["jupyter", "notebook", "--no-browser", "--port=8999"])
    time.sleep(5)

    kspecs_info = requests.get("http://localhost:8999/api/kernelspecs").json()

    kspecs = list(kspecs_info["kernelspecs"].keys())

    for kspec in kspecs:
        assert kspec in python_envs + r_envs

    nb.kill()
