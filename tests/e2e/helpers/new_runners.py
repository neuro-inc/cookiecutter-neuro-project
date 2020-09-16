import os
import re
import sys
import time
from typing import Callable, Any, Sequence, Tuple
from contextlib import contextmanager
from pathlib import Path
from more_itertools import unique_everseen


import pexpect

from tests.e2e.helpers.logs import log_msg, LOGGER

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


DEFAULT_TIMEOUT_LONG = 10 * 60

WIN = sys.platform == "win32"

try:
    TERM_WIDTH = os.get_terminal_size()[0]
except Exception as e:
    TERM_WIDTH = 100
    log_msg(f"Could not get terminal width: {e}, using default {TERM_WIDTH}")

if WIN:
    from pexpect.popen_spawn import PopenSpawn  # type: ignore

    _pexpect_spawn = PopenSpawn
else:
    _pexpect_spawn = pexpect.spawn



def _pexpect_isalive(proc: Any) -> bool:
    """ This method is a copy-paste of method `isalive()` somehow missing in Windows
    implementation of `pexpect`.
    Copy-paste from:
    https://github.com/pexpect/pexpect/blob/9e73fa87f60a66f31bfe137a4860722014a4afab/pexpect/fdpexpect.py#L77-L87
    """  # noqa
    if proc.child_fd == -1:
        return False
    try:
        os.fstat(proc.child_fd)
        return True
    except:  # noqa
        return False

class ExitCodeException(Exception):
    def __init__(self, exit_code: int):
        self._exit_code = exit_code

    def __str__(self) -> str:
        return f"Non-zero exit code: {self.exit_code}"

    @property
    def exit_code(self) -> int:
        return self._exit_code

def _hide_cmd_secret(cmd: str) -> str:
    args = cmd.split()
    for verb in VERBS_SECRET:
        try:
            idx = args.index(verb)
            return ' '.join(args[:idx+1] + ['<secret>'])
        except ValueError:
            pass
    return cmd


def _get_start_str(cmd: str, until: str) -> str:
    if until is pexpect.EOF:
        until = "<EOF>"
    else:
        until = f"'{until}'"
    s = f"$ {_hide_cmd_secret(cmd)}"
    s += f"  # until: {until} "
    s += "-" * (TERM_WIDTH - len(s))
    return s


def _get_end_str() -> str:
    s = "==" * (TERM_WIDTH // 2)
    return s


def run(cmd: str, *args, until: str = pexpect.EOF, verbose: bool = True, **kwargs) -> str:
    if verbose:
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
    if verbose:
        print(_get_end_str(), file=logfile)

    if until is pexpect.EOF:
        if _pexpect_isalive(child):
            # flush process buffer
            out += child.read()
            # wait for child to exit
            log_msg(f"Waiting for '{_hide_cmd_secret(cmd)}'", logger=LOGGER.info)
            child.wait()
        if not WIN:
            # On Windows, child does not have method `close()`, but it seems
            # it does not need it as it does not open a ptty connection
            child.close(force=True)
        if child.status:
            assert child.exitstatus != 0, "Here exit status should be non-zero!"
            if child.signalstatus is not None:
                log_msg(
                    f"Command '{_hide_cmd_secret(cmd)}' was killed "
                    f"via signal {child.signalstatus}",
                    logger=LOGGER.warning,
                )
            raise ExitCodeException(child.exitstatus)

    return out


def repeat_until_success(
    cmd: str,
    job_id: str,
    timeout_total_s: int = DEFAULT_TIMEOUT_LONG,
    interval_s: float = 1,
    **kwargs: Any,
) -> str:
    time_start = time.time()
    log_msg(f"Running command until success: `{_hide_cmd_secret(cmd)}`")
    while True:
        job_status = get_job_status(job_id)
        if job_status in JOB_STATUSES_TERMINATED:
            raise RuntimeError(f"Job {job_id} has terminated with status {job_status}")
        try:
            return run(cmd, **kwargs)
        except RuntimeError:
            pass
        time_current = time.time()
        if time_current - time_start > timeout_total_s:
            raise RuntimeError(f"Timeout exceeded: {time_current}")
        time.sleep(interval_s)

def get_job_status(job_id: str,verbose: bool = False) -> str:
    out = run(f"neuro status {job_id}", verbose=verbose)
    search = re.search(r"Status.*(" + "|".join(JOB_STATUSES_ALL) + ")", out)
    assert search, f"not found known job status in output: `{out}`"
    status = search.group(1)
    return status
