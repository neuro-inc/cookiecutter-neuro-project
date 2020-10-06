from tests.e2e.conftest import run


def test_neuro_flow_ps() -> None:
    proc = run("neuro-flow ps")
    assert proc.returncode == 0, proc
    assert not proc.stderr, proc
    assert "JOB" in proc.stdout, proc
