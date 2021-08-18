from tests.e2e.conftest import exec


def test_neuro_flow_ps() -> None:
    proc = exec("neuro-flow -v --show-traceback ps")
    assert proc.returncode == 0, proc
    assert not proc.stderr, proc
    assert "JOB" in proc.stdout, proc
