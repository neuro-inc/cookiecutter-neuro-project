import sys

from tests.e2e.conftest import exec


def test_neuro_flow_ps() -> None:
    proc = exec("neuro-flow -v --show-traceback ps")
    assert proc.returncode == 0, proc
    if sys.platform != "win32":
        # TODO: bug: on Windows neuro-flow prints to stderr
        # issue: https://github.com/neuro-inc/neuro-flow/issues/331
        assert not proc.stderr, proc
    assert "JOB" in proc.stdout, proc
