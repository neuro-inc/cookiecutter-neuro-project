import shlex
import subprocess


def exec(cmd: str, assert_exit_code: bool = True) -> "subprocess.CompletedProcess[str]":
    proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if assert_exit_code and proc.returncode != 0:
        raise RuntimeError(f"Non-zero exit code {proc.returncode} for `{cmd}`: {proc}")
    return proc
