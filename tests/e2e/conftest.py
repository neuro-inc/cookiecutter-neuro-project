import shlex
import subprocess
import typing as t


def exec(
    cmd: str, assert_exit_code: bool = True, env: dict[str, t.Any] | None = None
) -> "subprocess.CompletedProcess[str]":
    proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env=env,
    )
    if assert_exit_code and proc.returncode != 0:
        raise RuntimeError(f"Non-zero exit code {proc.returncode} for `{cmd}`: {proc}")
    return proc
