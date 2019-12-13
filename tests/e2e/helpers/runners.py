import re
import time
import typing as t
from pathlib import Path

import pexpect

from tests.e2e.configuration import (
    DEFAULT_ERROR_PATTERNS,
    DEFAULT_NEURO_ERROR_PATTERNS,
    DEFAULT_TIMEOUT_LONG,
    JOB_ID_DECLARATION_REGEX,
    JOB_STATUSES_TERMINATED,
    LOCAL_CLEANUP_JOBS_FILE,
    PEXPECT_BUFFER_SIZE_BYTES,
    PEXPECT_DEBUG_OUTPUT_LOGFILE,
    PROJECT_HIDDEN_FILES,
    TIMEOUT_NEURO_LS,
    TIMEOUT_NEURO_STATUS,
    VERBS_SECRET,
)
from tests.e2e.helpers.logs import LOGGER, log_msg
from tests.e2e.helpers.utils import log_errors_and_finalize, timeout


class ExitCodeException(Exception):
    def __init__(self, exit_code: int):
        self._exit_code = exit_code

    def __str__(self) -> str:
        return f"Non-zero exit code: {self.exit_code}"

    @property
    def exit_code(self) -> int:
        return self._exit_code


def run(
    cmd: str,
    *,
    attempts: int = 1,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    expect_patterns: t.Sequence[str] = (),
    error_patterns: t.Sequence[str] = (),
    verbose: bool = True,
    detect_new_jobs: bool = True,
    assert_exit_code: bool = True,
    skip_error_patterns_check: bool = False,
) -> str:
    """
    This procedure wraps method `_run`. If an exception raised, it repeats to run
    it so that overall the command `cmd` is executed not more than `attempts` times.
    """
    errors: t.List[Exception] = []
    while True:
        try:
            return _run(
                cmd,
                expect_patterns=expect_patterns,
                error_patterns=error_patterns,
                verbose=verbose,
                detect_new_jobs=detect_new_jobs,
                timeout_s=timeout_s,
                assert_exit_code=assert_exit_code,
                skip_error_patterns_check=skip_error_patterns_check,
            )
        except Exception as exc:
            errors.append(exc)
            num_retries = len(errors)
            if num_retries < attempts:
                log_msg(f"Retry #{num_retries}...")
            else:
                err_msg = (
                    f"Failed to run command `{cmd}` in {attempts} attempts."
                    " Errors:\n"
                )
                for err in errors:
                    err_msg += f"  {err}\n"
                raise RuntimeError(err_msg)


def _run(
    cmd: str,
    *,
    expect_patterns: t.Sequence[str] = (),
    error_patterns: t.Sequence[str] = (),
    verbose: bool = True,
    detect_new_jobs: bool = True,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    assert_exit_code: bool = True,
    skip_error_patterns_check: bool = False,
) -> str:
    """
    This method wraps method `run_once` and accepts all its named arguments.
    Once the command `cmd` is finished to be executed, the output is tested
    against the set of error patterns `error_patterns`, and if any of them
    was found, a `RuntimeError` will be raised.
    """
    with timeout(timeout_s):
        out = _run_once(
            cmd,
            expect_patterns,
            verbose=verbose,
            detect_new_jobs=detect_new_jobs,
            assert_exit_code=assert_exit_code,
        )
    if skip_error_patterns_check:
        all_error_patterns = list(error_patterns) + list(DEFAULT_ERROR_PATTERNS)
        errors = detect_errors(out, all_error_patterns, verbose=verbose)
        if errors:
            raise RuntimeError(f"Detected errors in output: {errors}")
    return out


def _run_once(
    cmd: str,
    expect_patterns: t.Sequence[str] = (),
    *,
    verbose: bool = True,
    detect_new_jobs: bool = True,
    assert_exit_code: bool = True,
) -> str:
    r"""
    This method runs a command `cmd` via `pexpect.spawn()`, and iteratively
    searches for patterns defined in `expect_patterns` *in their order*
    (normally, `pexpect.expect([pattern1, pattern2, ...])` won't search
    them in a specified order). If any expected pattern was not found,
    `RuntimeError` is raised. Use `verbose=True` to print useful information
    to log (also to dump all child process' output to the handler defined
    in `PEXPECT_DEBUG_OUTPUT_LOGFILE`).
    By default the method throws ExitCodeException if the process is killed or
    exits with non-zero exit code. Passing assert_exit_code=False suppresses this
    behavior.
    >>> # Expect the first and the last output:
    >>> _run_once("echo 1 2 3", expect_patterns=[r'1 \d+', '3'], verbose=False)
    '1 2 3'
    >>> # Abort once all the patterns have matched:
    >>> _run_once("bash -c 'echo 1 2 3 && sleep infinity'",
    ...     expect_patterns=['1', '2'], verbose=False)
    '1 2'
    >>> # Empty pattern list: read until the process returns:
    >>> _run_once('echo 1 2 3', expect_patterns=[], verbose=False)
    '1 2 3\r\n'
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
    >>> try:
    ...     _run_once('false', verbose=False)
    ...     assert False, "must be unreachable"
    ... except ExitCodeException as e:
    ...     assert e.exit_code == 1
    >>> # Suppress exit code check:
    >>> _run_once('false', verbose=False, assert_exit_code=False)
    """

    if verbose and not any(verb in cmd for verb in VERBS_SECRET):
        log_msg(f"<<< {cmd}")

    child = pexpect.spawn(
        cmd,
        timeout=DEFAULT_TIMEOUT_LONG,
        logfile=PEXPECT_DEBUG_OUTPUT_LOGFILE if verbose else None,
        maxread=PEXPECT_BUFFER_SIZE_BYTES,
        searchwindowsize=PEXPECT_BUFFER_SIZE_BYTES // 100,
        encoding="utf-8",
    )
    output = ""
    need_dump = False
    if not expect_patterns:
        # work until the process returns
        expect_patterns = [pexpect.EOF]
    else:
        if verbose:
            log_msg(f"Search patterns: {repr(expect_patterns)}")
    try:
        for expected in expect_patterns:
            try:
                child.expect(expected)
                if verbose:
                    log_msg(
                        "OK"
                        if expected is pexpect.EOF
                        else f"Found expected pattern: {repr(expected)}"
                    )
            except pexpect.ExceptionPexpect as e:
                need_dump = True
                if isinstance(e, pexpect.EOF):
                    err = f"NOT Found expected pattern: {repr(expected)}"
                elif isinstance(e, pexpect.TIMEOUT):
                    err = f"Timeout exceeded for command: {cmd}"
                else:
                    err = f"Pexpect error: {e}"
                if verbose:
                    log_msg(err, logger=LOGGER.error)
                raise RuntimeError(err)
            finally:
                chunk = _get_chunk(child)
                output += chunk
        if assert_exit_code:
            if child.isalive():
                # flush process buffer
                output += child.read()
                # wait for child to exit
                log_msg(f"Waiting for {cmd}", logger=LOGGER.info)
                child.wait()
            child.close(force=True)
            if child.status:
                need_dump = True
                if child.signalstatus is not None:
                    log_msg(f"{cmd} was killed via signal", logger=LOGGER.warning)
                raise ExitCodeException(child.status)
    finally:
        if detect_new_jobs:
            _dump_submitted_job_ids(_detect_job_ids(output))
        if verbose and need_dump:
            log_msg(f"DUMP: {repr(output)}")
    return output


def _get_chunk(child: pexpect.pty_spawn.spawn) -> str:
    chunk = child.before
    if isinstance(child.after, child.allowed_string_types):
        chunk += child.after
    return chunk


def detect_errors(
    output: str, error_patterns: t.Sequence[str] = (), *, verbose: bool = True
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
                if verbose:
                    log_msg(f"Detected error matching {repr(p)}: {repr(err)}")
    if verbose and found:
        log_msg(f"Overall {len(found)} patterns matched")
        log_msg(f"DUMP: {repr(output)}")
    return found


def _detect_job_ids(stdout: str) -> t.Set[str]:
    r"""
    >>> output = "Job ID: job-d8262adf-0dbb-4c40-bd80-cb42743f2453 Status: ..."
    >>> _detect_job_ids(output)
    {'job-d8262adf-0dbb-4c40-bd80-cb42743f2453'}
    >>> output = r"\x1b[1mJob ID\x1b[0m: job-d8262adf-0dbb-4c40-bd80-cb42743f2453 ..."
    >>> _detect_job_ids(output)
    {'job-d8262adf-0dbb-4c40-bd80-cb42743f2453'}
    """
    return set(JOB_ID_DECLARATION_REGEX.findall(stdout))


def _dump_submitted_job_ids(jobs: t.Iterable[str]) -> None:
    if jobs:
        log_msg(f"Dumped jobs: {jobs}")
        with LOCAL_CLEANUP_JOBS_FILE.open("a") as f:
            f.write("\n" + "\n".join(jobs))


def repeat_until_success(
    cmd: str,
    job_id: str,
    timeout_total_s: int = DEFAULT_TIMEOUT_LONG,
    interval_s: float = 1,
    **kwargs: t.Any,
) -> str:
    if not any(verb in cmd for verb in VERBS_SECRET):
        log_msg(f"Running command until success: `{cmd}`")
    with timeout(timeout_total_s):
        while True:
            job_status = get_job_status(job_id)
            if job_status in JOB_STATUSES_TERMINATED:
                raise RuntimeError(
                    f"Job {job_id} has terminated with status {job_status}"
                )
            try:
                return run(cmd, **kwargs)
            except RuntimeError:
                pass
            time.sleep(interval_s)


# == execution helpers ==


def try_except_finally(*finalizer_commands: str) -> t.Callable[..., t.Any]:
    def callback() -> None:
        for cmd in finalizer_commands:
            run(cmd, verbose=True, error_patterns=())

    def decorator(func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        # NOTE(artem) due to specifics of pytest fixture implementations,
        #  this decorator won't work directly on test functions with fixtures
        #  (use a separate function, see for example `test_make_setup`)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> None:
            with log_errors_and_finalize(callback if finalizer_commands else None):
                func(*args, **kwargs)

        return wrapper

    return decorator


# == neuro helpers ==


def parse_job_id(out: str) -> str:
    search = re.search(JOB_ID_DECLARATION_REGEX, out)
    assert search, f"not found job-ID in output: `{out}`"
    return search.group(1)


def parse_job_url(out: str) -> str:
    search = re.search(r"Http URL.*: (https://.+neu\.ro)", out)
    assert search, f"not found URL in output: `{out}`"
    return search.group(1)


def neuro_ls(path: str) -> t.Set[str]:
    out = run(
        f"neuro ls {path}",
        timeout_s=TIMEOUT_NEURO_LS,
        verbose=True,
        error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    result = set(out.split())
    for hidden in PROJECT_HIDDEN_FILES:
        if hidden in result:
            result.remove(hidden)
    return result


def neuro_rm_dir(
    path: str, timeout_s: int = DEFAULT_TIMEOUT_LONG, verbose: bool = False
) -> None:
    log_msg(f"Deleting remote directory `{path}`")
    run(f"neuro rm -r {path}", timeout_s=timeout_s, verbose=verbose)
    log_msg("Done.")


def wait_job_change_status_to(
    job_id: str,
    target_status: str,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    delay_s: int = 1,
) -> None:
    log_msg(f"Waiting for job {job_id} to get status {target_status}...")
    with timeout(timeout_s):
        while True:
            status = get_job_status(job_id)
            if status == target_status:
                log_msg("Done.")
                return
            if status in JOB_STATUSES_TERMINATED:
                raise RuntimeError(
                    f"Unexpected terminated job status: {job_id}, {status}"
                )
            time.sleep(delay_s)


def get_job_status(job_id: str) -> str:
    out = run(
        f"neuro status {job_id}",
        timeout_s=TIMEOUT_NEURO_STATUS,
        verbose=False,
        error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    search = re.search(r"Status: (\w+)", out)
    assert search, f"not found job status in output: `{out}`"
    status = search.group(1)
    return status


def ls_files(local_path: t.Union[Path, str]) -> t.Set[str]:
    path = Path(local_path)
    assert path.is_dir(), f"path {path} does not exist"
    return {
        f.name
        for f in path.iterdir()
        if f.is_file() and f.name not in PROJECT_HIDDEN_FILES
    }


def ls_dirs(local_path: t.Union[Path, str]) -> t.Set[str]:
    path = Path(local_path)
    assert path.is_dir(), f"path {path} does not exist"
    return {
        f.name
        for f in path.iterdir()
        if f.is_dir() and f.name not in PROJECT_HIDDEN_FILES
    }
