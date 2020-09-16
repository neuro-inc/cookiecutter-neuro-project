import os
import re
import sys
import time
from typing import Callable, Any, Sequence
from contextlib import contextmanager
from pathlib import Path
from more_itertools import unique_everseen


import pexpect

from tests.e2e.helpers.logs import log_msg

_pexpect_spawn: Callable[..., Any]

VERBS_SECRET = ("login-with-token",)
VERBS_JOB_RUN = ("run", "submit")
JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"
JOB_STATUSES_TERMINATED = (
    JOB_STATUS_SUCCEEDED,
    JOB_STATUS_FAILED,
    JOB_STATUS_CANCELLED,
)
JOB_STATUSES_ALL = (
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    JOB_STATUS_FAILED,
    JOB_STATUS_CANCELLED,
)
JOB_ID_PATTERN = (
    r"job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
JOB_ID_DECLARATION_REGEX = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    JOB_ID_PATTERN,
    re.IGNORECASE,
)


DEFAULT_TIMEOUT_LONG = 3 * 60

WIN = sys.platform == "win32"

TERM_WIDTH = os.get_terminal_size()[0]

if WIN:
    from pexpect.popen_spawn import PopenSpawn  # type: ignore

    _pexpect_spawn = PopenSpawn
else:
    _pexpect_spawn = pexpect.spawn


def _get_start_str(cmd: str, until: str) -> str:
    if until is pexpect.EOF:
        until = "<EOF>"
    else:
        until = f"'{until}'"
    s = f"$ {cmd}"
    s += f"  # until: {until} "
    s += "-" * (TERM_WIDTH - len(s))
    return s


def _get_end_str() -> str:
    s = "==" * (TERM_WIDTH // 2)
    return s


def run(cmd: str, *, until: str = pexpect.EOF, to_stdout: bool = True) -> str:
    if to_stdout:
        logfile = sys.stdout
        print(_get_start_str(cmd, until), file=logfile)
    else:
        logfile = None

    child = _pexpect_spawn(
        cmd, encoding="utf-8", logfile=logfile, timeout=DEFAULT_TIMEOUT_LONG,
    )
    child.expect(until)
    out = child.before
    if isinstance(child.after, child.allowed_string_types):
        out += child.after
    if to_stdout:
        print(_get_end_str(), file=logfile)
    return out
