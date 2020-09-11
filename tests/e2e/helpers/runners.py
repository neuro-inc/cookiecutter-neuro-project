import os
import re
import sys
import time
import typing as t
from contextlib import contextmanager
from pathlib import Path

import pexpect
from more_itertools import unique_everseen

from tests.e2e.configuration import (
    DEFAULT_ERROR_PATTERNS,
    DEFAULT_NEURO_ERROR_PATTERNS,
    DEFAULT_TIMEOUT_LONG,
    DEFAULT_TIMEOUT_SHORT,
    JOB_ID_DECLARATION_REGEX,
    JOB_STATUSES_ALL,
    JOB_STATUSES_TERMINATED,
    LOGFILE_PATH,
    PEXPECT_BUFFER_SIZE_BYTES,
    VERBS_SECRET,
)
from tests.e2e.helpers.logs import LOGGER, log_msg


WIN = sys.platform == "win32"


class ExitCodeException(Exception):
    def __init__(self, exit_code: int):
        self._exit_code = exit_code

    def __str__(self) -> str:
        return f"Non-zero exit code: {self.exit_code}"

    @property
    def exit_code(self) -> int:
        return self._exit_code


_pexpect_spawn: t.Callable[..., t.Any]

if WIN:
    from pexpect.popen_spawn import PopenSpawn  # type: ignore

    _pexpect_spawn = PopenSpawn
else:
    _pexpect_spawn = pexpect.spawn


def _pexpect_isalive(proc: t.Any) -> bool:
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


def run(
    cmd: str,
    *,
    expect_patterns: t.Sequence[str] = (),
    error_patterns: t.Sequence[str] = (),
    verbose: bool = True,
    assert_exit_code: bool = True,
    check_default_errors: bool = True,
) -> str:
    """
    This method wraps method `_run_once` and accepts all its named arguments.
    Once the command `cmd` is finished to be executed, the output is tested
    against the set of error patterns `error_patterns`, and if any of them
    was found, a `RuntimeError` will be raised.
    """
    if _expects_default_errors(expect_patterns):
        check_default_errors = False

    out = _run_once(
        cmd,
        expect_patterns=expect_patterns,
        verbose=verbose,
        assert_exit_code=assert_exit_code,
    )
    all_error_patterns = list(error_patterns)
    if check_default_errors:
        all_error_patterns += list(DEFAULT_ERROR_PATTERNS)

    errors = detect_errors(out, all_error_patterns, verbose=verbose)
    if errors:
        raise RuntimeError(f"Detected errors in output: {errors}")
    return out


def _expects_default_errors(expect_patterns: t.Sequence[str] = ()) -> bool:
    """
    >>> _expects_default_errors(["ERROR: bla-bla"])
    True
    >>> _expects_default_errors(["Error: bla-bla"])
    True
    >>> _expects_default_errors([r"Makefile:.+ recipe for target '_check_setup' failed"])
    True
    >>> _expects_default_errors(["Not an error"])
    False
    """  # noqa
    return any(
        re.search(error_pattern, success_pattern)
        for error_pattern in DEFAULT_ERROR_PATTERNS
        for success_pattern in expect_patterns
    )


def _run_once(
    cmd: str,
    *,
    expect_patterns: t.Sequence[str] = (),
    verbose: bool = True,
    assert_exit_code: bool = True,
) -> str:
    r"""
    This method runs a command `cmd` via `pexpect.spawn()`, and iteratively
    searches for patterns defined in `expect_patterns` *in their order*
    (normally, `pexpect.expect([pattern1, pattern2, ...])` won't search
    them in a specified order). If any expected pattern was not found,
    `RuntimeError` is raised. Use `verbose=True` to print useful information
    to log (also to dump all child process' output to the handler defined
    in `LOGFILE_PATH`).
    By default the method throws ExitCodeException if the process is killed or
    exits with non-zero exit code. Passing assert_exit_code=False suppresses this
    behavior.
    >>> # Expect the first and the last output:
    >>> _run_once("echo 1 2 3", expect_patterns=[r'1 \d+', '3'], verbose=False).strip()
    '1 2 3'
    >>> # Abort once all the patterns have matched:
    >>> _run_once("bash -c 'echo 1 2 3 && sleep infinity'", expect_patterns=['1', '2'], assert_exit_code=False, verbose=False).strip()
    '1 2'
    >>> # Empty pattern list: read until the process returns:
    >>> _run_once('echo 1 2 3', expect_patterns=[], verbose=False).strip()
    '1 2 3'
    >>> # Wrong order of patterns:
    >>> try:
    ...     _run_once('echo 1 2 3', expect_patterns=['3', '1'], verbose=False)
    ...     assert False, "must be unreachable"
    ... except RuntimeError as e:
    ...     assert str(e) == "NOT Found expected pattern: '1'", repr(str(e))
    >>> # Pattern not found at all:
    >>> try:
    ...     _run_once('echo 1 2 3', expect_patterns=['4'], verbose=False)
    ...     assert False, "must be unreachable"
    ... except RuntimeError as e:
    ...     assert str(e) == "NOT Found expected pattern: '4'", repr(str(e))
    >>> # Exit code:
    >>> _run_once('false', verbose=False, assert_exit_code=False)
    ''
    >>> try:
    ...     _run_once('false', verbose=False)
    ...     assert False, "must be unreachable"
    ... except ExitCodeException as e:
    ...     assert e.exit_code == 1, e.exit_code
    >>> # Suppress exit code check:
    >>> _run_once('false', verbose=False, assert_exit_code=False)
    ''
    """  # noqa
    log_msg(f"<<< {_hide_secret_cmd(cmd)}")

    output = ""
    need_dump = False
    logfile: t.Optional[t.IO[str]] = None
    try:
        logfile = LOGFILE_PATH.open("a")
        child = _pexpect_spawn(
            cmd,
            logfile=logfile,
            maxread=PEXPECT_BUFFER_SIZE_BYTES,
            encoding="utf-8",
            timeout=DEFAULT_TIMEOUT_LONG,
        )
        if not expect_patterns:
            # work until the process returns
            expect_patterns = [pexpect.EOF]
        else:
            log_msg(f"Search patterns: {repr(expect_patterns)}")

        for expected in expect_patterns:
            try:
                child.expect(expected)
                if verbose and expected is not pexpect.EOF:
                    log_msg(f"Found expected pattern: {repr(expected)}")
            except pexpect.ExceptionPexpect as e:
                need_dump = True
                if isinstance(e, pexpect.EOF):
                    err = f"NOT Found expected pattern: {repr(expected)}"
                elif isinstance(e, pexpect.TIMEOUT):
                    err = f"Timeout exceeded for command: '{_hide_secret_cmd(cmd)}'"
                else:
                    err = f"Pexpect error: {e}"
                log_msg(err, logger=LOGGER.error)
                raise RuntimeError(err)
            finally:
                chunk = child.before
                if isinstance(child.after, child.allowed_string_types):
                    chunk += child.after
                detected = list(
                    unique_everseen(JOB_ID_DECLARATION_REGEX.findall(chunk))
                )
                if detected:
                    log_msg(f"Jobs: {detected}")
                output += chunk
        if assert_exit_code:
            if _pexpect_isalive(child):
                # flush process buffer
                output += child.read()
                # wait for child to exit
                log_msg(f"Waiting for '{_hide_secret_cmd(cmd)}'", logger=LOGGER.info)
                child.wait()
            if not WIN:
                # On Windows, child does not have method `close()`, but it seems
                # it does not need it as it does not open a ptty connection
                child.close(force=True)
            if child.status:
                assert child.exitstatus != 0, "Here exit status should be non-zero!"
                need_dump = True
                if child.signalstatus is not None:
                    log_msg(
                        f"Command '{_hide_secret_cmd(cmd)}' was killed "
                        f"via signal {child.signalstatus}",
                        logger=LOGGER.warning,
                    )
                raise ExitCodeException(child.exitstatus)
    finally:
        if need_dump:
            log_msg(f"DUMP: {repr(output)}")
        if logfile:
            logfile.flush()
            logfile.close()
    return output


def _is_command_secret(cmd: str) -> bool:
    return any(verb in cmd for verb in VERBS_SECRET)


def _hide_secret_cmd(cmd: str) -> str:
    """
    >>> _hide_secret_cmd("neuro login-with-token secret.jwt.token")
    'neuro login-with-token secret.<hidden>'
    """
    return cmd if not _is_command_secret(cmd) else cmd[:30] + "<hidden>"


def detect_errors(
    output: str, error_patterns: t.Sequence[str], *, verbose: bool = True
) -> t.Set[str]:
    r"""
    >>> output = r"1\r\n2\r\n3\r\n"
    >>> errs = detect_errors(output, error_patterns=['2'], verbose=False)
    >>> assert errs == {'2'}, repr(errs)
    >>> errs = detect_errors(output, error_patterns=['3', '(2|3)'], verbose=False)
    >>> assert errs == {'2', '3'}, repr(errs)
    >>> errs = detect_errors(output, error_patterns=['3', r'\d+'], verbose=False)
    >>> assert errs == {'1', '2', '3'}, repr(errs)
    """
    if not error_patterns:
        return set()

    found = set()
    for p in error_patterns:
        for err in re.findall(p, output):
            if err:
                found.add(err)
                log_msg(f"Detected error matching {repr(p)}: {repr(err)}")
    if found:
        log_msg(f"Overall {len(found)} patterns matched")
        log_msg(f"DUMP: {repr(output)}")
    return found


def repeat_until_success(
    cmd: str,
    job_id: str,
    timeout_total_s: int = DEFAULT_TIMEOUT_SHORT,
    interval_s: float = 1,
    **kwargs: t.Any,
) -> str:
    time_start = time.time()
    if not _is_command_secret(cmd):
        log_msg(f"Running command until success: `{cmd}`")
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


# == execution helpers ==


@contextmanager
def finalize(*finally_commands: str):  # type: ignore
    try:
        yield
    except Exception as e:
        log_msg("=" * 100, logger=LOGGER.error)
        log_msg(f"Error: {e.__class__}: {e}", logger=LOGGER.error)
        log_msg("=" * 100, logger=LOGGER.error)
        raise
    finally:
        for cmd in finally_commands:
            log_msg(f"Running finalization command '{_hide_secret_cmd(cmd)}'")
            run(cmd, verbose=False, assert_exit_code=False)


# == neuro helpers ==


def parse_job_id(out: str) -> str:
    search = re.search(JOB_ID_DECLARATION_REGEX, out)
    assert search, f"not found job-ID in output: `{out}`"
    return search.group()


def parse_jobs_ids(out: str, expect_num: int) -> t.List[str]:
    jobs = re.findall(JOB_ID_DECLARATION_REGEX, out)
    assert len(jobs) == expect_num, f"not found some job-IDs in output: `{out}`"
    return jobs


def parse_job_url(out: str) -> str:
    search = re.search(r"Http URL.*:.*(https://.+neu\.ro)", out)
    if search:
        url = search.group(1)
        log_msg(f"Found URL: `{url}`")
        return url
    else:
        raise RuntimeError(f"Not found URL in output: `{out}`")


def neuro_ls(path: str, hidden: bool = True) -> t.Set[str]:
    options: t.List[str] = []
    if hidden:
        options.append("-a")
    out = run(
        f"neuro ls {' '.join(options)} {path}",
        error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    return set(out.split())


def neuro_rm_dir(path: str) -> None:
    log_msg(f"Deleting remote directory `{path}`")
    run(f"neuro rm -r {path}")
    log_msg("Done.")


def wait_job_change_status_to(
    job_id: str,
    target_status: str,
    timeout_total_s: int = DEFAULT_TIMEOUT_LONG,
    delay_s: int = 1,
    verbose: bool = True,
) -> None:
    log_msg(f"Waiting for job {job_id} to get status: '{target_status}'...")
    time_start = time.time()
    while True:
        status = get_job_status(job_id, verbose=verbose)
        log_msg(f"Got status: `{status}`")
        if status == target_status:
            log_msg(f"Job {job_id} reached status '{target_status}'")
            return
        if status in JOB_STATUSES_TERMINATED:
            raise RuntimeError(
                f"Unexpected terminated job status: {job_id}, '{status}'"
            )
        time_current = time.time()
        if time_current - time_start > timeout_total_s:
            raise RuntimeError(f"Timeout exceeded: {time_current}")
        time.sleep(delay_s)


def get_job_status(job_id: str, verbose: bool = False) -> str:
    out = run(
        f"neuro status {job_id}",
        verbose=verbose,
        error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    search = re.search(r"Status.*(" + "|".join(JOB_STATUSES_ALL) + ")", out)
    assert search, f"not found known job status in output: `{out}`"
    status = search.group(1)
    return status


def ls(local_path: t.Union[Path, str], hidden: bool = True) -> t.Set[str]:
    path = Path(local_path)
    assert path.is_dir(), f"path {path} does not exist"
    return {p.name for p in path.iterdir() if not hidden or not p.name.startswith(".")}
