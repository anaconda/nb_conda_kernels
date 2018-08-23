from subprocess import check_output, CalledProcessError
from notebook.services.kernelspecs.tests import test_kernelspecs_api

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch  # py2


CONDA_INFO_ARGS = ["conda", "info", "--json"]


class APITest(test_kernelspecs_api.APITest):
    """ Run all the upstream tests."""
    pass


class BadCondaAPITest(test_kernelspecs_api.APITest):
    @classmethod
    def setup_class(cls):
        def _mock_check_output(cmd, *args, **kwargs):
            if cmd == CONDA_INFO_ARGS:
                raise CalledProcessError("bad conda")

            return check_output(cmd, *args, **kwargs)

        cls.cond_info_patch = patch("subprocess.check_output",
                                    _mock_check_output)
        cls.cond_info_patch.start()
        super(BadCondaAPITest, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(BadCondaAPITest, cls).teardown_class()
        cls.cond_info_patch.stop()

    def test_no_conda_kernels(self):
        model = self.ks_api.list().json()
        self.assertEquals(
            [],
            [name for name in model["kernelspecs"].keys()
             if name.startswith("conda-")]
        )
