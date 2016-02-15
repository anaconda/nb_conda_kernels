import json
import requests
import subprocess
import time

from os.path import split

from selenium import webdriver


def _setup():
    """Build envs names from conda info envs"""
    p = subprocess.check_output(["conda", "info", "--json"]).decode("utf-8")
    conda_info = json.loads(p)
    envs = [split(base)[1] for base in conda_info["envs"]]
    envs.append("Root")
    python_envs = ["Python [{}]".format(env) for env in envs]
    r_envs = ["R [{}]".format(env) for env in envs]

    return python_envs, r_envs


def _notebook():
    """Start the notebook server"""
    nb = subprocess.Popen(["jupyter", "notebook", "--no-browser", "--port=8999"])
    time.sleep(5)

    return nb


def _get_kspecs():
    """Ping the REST point to get kernelspecs info"""
    kspecs_info = requests.get("http://localhost:8999/api/kernelspecs").json()
    kspecs = list(kspecs_info["kernelspecs"].keys())

    return kspecs


def _refresh():
    driver = webdriver.Firefox()
    driver.get("http://localhost:8999/api/kernelspecs")
    driver.refresh()


def test_kernel_specs():
    """Test if the kernelspecs created on the fly belongs to the _setup set"""
    python_envs, r_envs = _setup()
    nb = _notebook()
    kspecs = _get_kspecs()

    for kspec in kspecs:
        assert kspec in python_envs + r_envs

    nb.kill()


def test_kernel_specs_update():
    """Test if updating envs is detected by our manager creating the
    corresponfing kernelspec"""
    python_envs, r_envs = _setup()
    nb = _notebook()
    kspecs = _get_kspecs()

    updated_py_env = "Python [{}]".format("_test_nb_conda_kernels")
    assert updated_py_env not in kspecs

    subprocess.Popen(["conda", "create", "-n", "_test_nb_conda_kernels", "ipykernel", "--yes"])

    _refresh()

    kspecs = _get_kspecs()
    print("py_env", updated_py_env)
    print("kspecs", kspecs)
    assert updated_py_env in kspecs

    subprocess.Popen(["conda", "env", "remove",  "-n", "_test_nb_conda_kernels", "--yes"])
    time.sleep(5)

    nb.kill()
