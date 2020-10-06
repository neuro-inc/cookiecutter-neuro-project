from tests.e2e.conftest import run_cmd


def test_neuro_flow_ps() -> None:
    proc = run_cmd("neuro-flow ps")
    assert proc.returncode == 0, proc
    assert not proc.stderr, proc
    assert "JOB" in proc.stdout, proc
