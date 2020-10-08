from tests.e2e.conftest import exec


def test_neuro_flow_ps() -> None:
    print(exec("pwd").stdout)
    print(exec("ls").stdout)
    proc = exec("neuro-flow ps")
    assert proc.returncode == 0, proc
    assert not proc.stderr, proc
    assert "JOB" in proc.stdout, proc
