import logging
import os
import re
import shutil
import signal
import textwrap
import time
import typing as t
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path

import pexpect
import pytest

from tests.e2e.configuration import (
    DEFAULT_ERROR_PATTERNS,
    DEFAULT_NEURO_ERROR_PATTERNS,
    DEFAULT_TIMEOUT_LONG,
    FILE_SIZE_B,
    JOB_ID_DECLARATION_PATTERN,
    JOB_STATUSES_TERMINATED,
    LOCAL_PROJECT_CONFIG_PATH,
    LOCAL_ROOT_PATH,
    LOCAL_SUBMITTED_JOBS_FILE,
    LOCAL_TESTS_SAMPLES_PATH,
    MK_CODE_PATH,
    MK_DATA_PATH,
    MK_NOTEBOOKS_PATH,
    MK_PROJECT_PATH_STORAGE,
    MK_PROJECT_SLUG,
    N_FILES,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PEXPECT_BUFFER_SIZE_BYTES,
    PEXPECT_DEBUG_OUTPUT_LOGFILE,
    PROJECT_APT_FILE_NAME,
    PROJECT_HIDDEN_FILES,
    PROJECT_PIP_FILE_NAME,
    TIMEOUT_NEURO_LOGIN,
    TIMEOUT_NEURO_LS,
    TIMEOUT_NEURO_STATUS,
    UNIQUE_PROJECT_NAME,
    VERBS_SECRET,
    unique_label,
)
from tests.utils import inside_dir


# == pytest config ==


def pytest_logger_config(logger_config: t.Any) -> None:
    """Pytest logging setup"""
    loggers = [LOGGER_NAME]
    logger_config.add_loggers(loggers, stdout_level="info")
    logger_config.set_log_option_default(",".join(loggers))


# == logging ==

LOGGER_NAME = "e2e"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    return logger


log = get_logger()


# == general helpers ==


def log_msg(msg: str, *, logger: t.Callable[..., None] = log.info) -> None:
    logger(msg)
    PEXPECT_DEBUG_OUTPUT_LOGFILE.write(msg + "\n")


@contextmanager
def timeout(time_s: int) -> t.Iterator[None]:
    """ source: https://www.jujens.eu/posts/en/2018/Jun/02/python-timeout-function/
    """

    def raise_timeout(signum: int, frame: t.Any) -> t.NoReturn:
        raise TimeoutError

    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time_s)

    try:
        yield
    except TimeoutError:
        log_msg(f"TIMEOUT ERROR: {time_s} sec", logger=log.error)
        raise
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


@contextmanager
def measure_time(command_name: str = "") -> t.Iterator[None]:
    log_msg("=" * 100)
    start_time = time.time()
    log_msg(f"Measuring time for command: `{command_name}`")
    yield
    elapsed_time = time.time() - start_time
    log_msg("=" * 50)
    log_msg(f"  TIME SUMMARY [{command_name}]: {elapsed_time:.2f} sec")
    log_msg("=" * 50)


@contextmanager
def log_errors_and_finalize(
    finalizer_callback: t.Optional[t.Callable[[], t.Any]] = None
) -> t.Iterator[None]:
    try:
        yield
    except Exception as e:
        log_msg("-" * 100, logger=log.error)
        log_msg(f"Error: {e.__class__}: {e}", logger=log.error)
        log_msg("-" * 100, logger=log.error)
        raise
    finally:
        if finalizer_callback is not None:
            log_msg("Running finalization callback...")
            finalizer_callback()
            log_msg("Done")


# == fixtures ==

ClientConfig = namedtuple("ClientConfig", "url token")


def pytest_addoption(parser: t.Any) -> None:
    parser.addoption(
        "--environment",
        action="store",
        metavar="NAME",
        help="run e2e tests against the environment NAME (dev, staging, ...)",
    )


def pytest_configure(config: t.Any) -> None:
    # register an additional marker
    config.addinivalue_line(
        "markers", "env(name): mark test to run only on named environment"
    )


@pytest.fixture(scope="session")
def client_setup_factory(request: t.Any) -> t.Callable[[], ClientConfig]:
    def _f() -> ClientConfig:
        environment = request.config.getoption("--environment", "dev")
        if environment == "dev":
            env_name_token = "COOKIECUTTER_TEST_E2E_DEV_TOKEN"
            env_name_url = "COOKIECUTTER_TEST_E2E_DEV_URL"
        elif environment == "staging":
            env_name_token = "COOKIECUTTER_TEST_E2E_STAGING_TOKEN"
            env_name_url = "COOKIECUTTER_TEST_E2E_STAGING_URL"
        else:
            raise ValueError(f"Invalid environment: {environment}")
        return ClientConfig(
            token=os.environ[env_name_token], url=os.environ[env_name_url]
        )

    return _f


@pytest.fixture(scope="session", autouse=True)
def change_directory_to_temp(tmpdir_factory: t.Any) -> t.Iterator[None]:
    tmp = tmpdir_factory.mktemp("test-cookiecutter")
    with inside_dir(str(tmp)):
        yield


@pytest.fixture(scope="session", autouse=True)
def cookiecutter_setup(change_directory_to_temp: None) -> t.Iterator[None]:
    run(
        f"cookiecutter --no-input --config-file={LOCAL_PROJECT_CONFIG_PATH} "
        f'{LOCAL_ROOT_PATH} project_name="{UNIQUE_PROJECT_NAME}"',
        error_patterns=["raise .*Exception"],
        verbose=False,
    )
    with inside_dir(MK_PROJECT_SLUG):
        yield


@pytest.fixture(scope="session", autouse=True)
def generate_empty_project(cookiecutter_setup: None) -> None:
    log_msg(f"Initializing empty project: `{Path().absolute()}`")

    apt_file = Path(PROJECT_APT_FILE_NAME)
    log_msg(f"Copying `{apt_file}`")
    assert apt_file.is_file() and apt_file.exists()
    with apt_file.open("a") as f:
        for package in PACKAGES_APT_CUSTOM:
            f.write("\n" + package)

    pip_file = Path(PROJECT_PIP_FILE_NAME)
    log_msg(f"Copying `{pip_file}`")
    assert pip_file.is_file() and pip_file.exists()
    with pip_file.open("a") as f:
        for package in PACKAGES_PIP_CUSTOM:
            f.write("\n" + package)

    data_dir = Path(MK_DATA_PATH)
    log_msg(f"Generating data to `{data_dir}/`")
    assert data_dir.is_dir() and data_dir.exists()
    for _ in range(N_FILES):
        generate_random_file(data_dir, FILE_SIZE_B)
    assert len(list(data_dir.iterdir())) >= N_FILES

    code_dir = Path(MK_CODE_PATH)
    log_msg(f"Generating code files to `{code_dir}/`")
    assert code_dir.is_dir() and code_dir.exists()
    code_file = code_dir / "main.py"
    with code_file.open("w") as f:
        f.write(
            textwrap.dedent(
                """\
        if __name__ == "__main__":
            print("test script")
        """
            )
        )
    assert code_file.exists()

    notebooks_dir = Path(MK_NOTEBOOKS_PATH)
    assert notebooks_dir.is_dir() and notebooks_dir.exists()
    copy_local_files(LOCAL_TESTS_SAMPLES_PATH, notebooks_dir)
    assert list(notebooks_dir.iterdir())


@pytest.fixture(scope="session", autouse=True)
def pip_install_neuromation(generate_empty_project: None) -> None:
    run("pip install -U neuromation", verbose=False)
    assert "Name: neuromation" in run("pip show neuromation", verbose=False)


@pytest.fixture(scope="session", autouse=True)
def neuro_login(
    pip_install_neuromation: None, client_setup_factory: t.Callable[[], ClientConfig]
) -> t.Iterator[None]:
    config = client_setup_factory()
    captured = run(
        f"neuro config login-with-token {config.token} {config.url}",
        timeout_s=TIMEOUT_NEURO_LOGIN,
        verbose=False,
    )
    assert f"Logged into {config.url}" in captured, f"stdout: `{captured}`"
    time.sleep(0.5)  # sometimes flakes  # TODO: remove this sleep
    log_msg(run("neuro config show", verbose=False))
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup(neuro_login: None) -> t.Iterator[None]:
    try:
        yield
    finally:
        log_msg("-" * 100)
        _cleanup_jobs()
        _cleanup_storage()


def _cleanup_jobs() -> None:
    log_msg("Cleanup jobs...")
    try:
        path = LOCAL_SUBMITTED_JOBS_FILE.absolute()
        out = run(f"bash -c '[ -f {path} ] && cat {path} || true'")
        if out:
            run(
                f"bash -c 'neuro kill $(cat {path})'",
                detect_new_jobs=False,
                verbose=True,
            )
    except Exception as e:
        log_msg(f"Failed to cleanup jobs: {e}", logger=log.error)
    finally:
        log_msg(f"Result: {run('neuro ps', detect_new_jobs=False, verbose=False)}")


def _cleanup_storage() -> None:
    log_msg("Cleanup storage...")
    try:
        neuro_rm_dir(MK_PROJECT_PATH_STORAGE, ignore_errors=True, verbose=True)
    except Exception as e:
        log_msg(f"Failed to cleanup storage: {e}", logger=log.error)
    finally:
        log_msg(f"Result: {run('neuro ls', verbose=False)}")


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


def run(
    cmd: str,
    *,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    expect_patterns: t.Sequence[str] = (),
    error_patterns: t.Sequence[str] = DEFAULT_ERROR_PATTERNS,
    verbose: bool = True,
    detect_new_jobs: bool = True,
) -> str:
    """
    This method wraps method `run_once` and accepts all its named arguments.
    Once the command `cmd` is finished to be executed, the output is tested
    against the set of error patterns `error_patterns`, and if any of them
    was found, a `RuntimeError` will be raised.
    """
    with timeout(timeout_s):
        out = _run_once(
            cmd, expect_patterns, verbose=verbose, detect_new_jobs=detect_new_jobs
        )
    errors = detect_errors(out, error_patterns, verbose=verbose)
    if errors:
        raise RuntimeError(f"Detected errors in output: {errors}")
    return out


def _run_once(
    cmd: str,
    expect_patterns: t.Sequence[str] = (),
    *,
    verbose: bool = True,
    detect_new_jobs: bool = True,
) -> str:
    r"""
    This method runs a command `cmd` via `pexpect.spawn()`, and iteratively
    searches for patterns defined in `expect_patterns` *in their order*
    (normally, `pexpect.expect([pattern1, pattern2, ...])` won't search
    them in a specified order). If any expected pattern was not found,
    `RuntimeError` is raised. Use `verbose=True` to print useful information
    to log (also to dump all child process' output to the handler defined
    in `PEXPECT_DEBUG_OUTPUT_LOGFILE`).
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
    """

    if verbose and not any(verb in cmd for verb in VERBS_SECRET):
        log_msg(f"[.] Running command: `{cmd}`")

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
                    log_msg(f"Found expected pattern: {repr(expected)}")
            except pexpect.ExceptionPexpect as e:
                need_dump = True
                if isinstance(e, pexpect.EOF):
                    err = f"NOT Found expected pattern: {repr(expected)}"
                elif isinstance(e, pexpect.TIMEOUT):
                    err = f"Timeout exceeded for command: {cmd}"
                else:
                    err = f"Pexpect error: {e}"
                if verbose:
                    log_msg(err, logger=log.error)
                raise RuntimeError(err)
            finally:
                chunk = _get_chunk(child)
                output += chunk
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
    return set(JOB_ID_DECLARATION_PATTERN.findall(stdout))


def _dump_submitted_job_ids(jobs: t.Iterable[str]) -> None:
    if jobs:
        log_msg(f"Dumped jobs: {jobs}")
        with LOCAL_SUBMITTED_JOBS_FILE.open("a") as f:
            f.write("\n" + "\n".join(jobs))


# == local file helpers ==


def generate_random_file(path: Path, size_b: int) -> Path:
    name = f"{unique_label()}.tmp"
    path_and_name = path / name
    with path_and_name.open("wb") as file:
        generated = 0
        while generated < size_b:
            length = min(1024 * 1024, size_b - generated)
            data = os.urandom(length)
            file.write(data)
            generated += len(data)
    return path_and_name


def cleanup_local_dirs(*dirs: t.Union[str, Path]) -> None:
    for d_or_name in dirs:
        if isinstance(d_or_name, str):
            d = Path(d_or_name)
        else:
            d = d_or_name
        log_msg(f"Cleaning up local directory `{d.absolute()}`")
        for f in d.iterdir():
            if f.is_file():
                f.unlink()
        assert not list(d.iterdir()), "directory should be empty here"


def copy_local_files(from_dir: Path, to_dir: Path) -> None:
    for f in from_dir.glob("*"):
        if not f.is_file():
            continue
        target = to_dir / f.name
        if target.exists():
            log_msg(f"Target `{target.absolute()}` already exists")
            continue
        log_msg(f"Copying file `{f}` to `{target.absolute()}`")
        shutil.copyfile(str(f), target, follow_symlinks=False)


# == neuro helpers ==


def parse_job_id(out: str) -> str:
    search = re.search(JOB_ID_DECLARATION_PATTERN, out)
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
        verbose=False,
        error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    result = set(out.split())
    for hidden in PROJECT_HIDDEN_FILES:
        if hidden in result:
            result.remove(hidden)
    return result


def neuro_rm_dir(
    project_relative_path: str,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    ignore_errors: bool = False,
    verbose: bool = False,
) -> None:
    log_msg(f"Deleting remote directory `{project_relative_path}`")
    run(
        f"neuro rm -r {project_relative_path}",
        timeout_s=timeout_s,
        verbose=verbose,
        error_patterns=[] if ignore_errors else list(DEFAULT_NEURO_ERROR_PATTERNS),
    )
    log_msg("Done.")


def wait_job_change_status_to(
    job_id: str,
    target_status: str,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    delay_s: int = 1,
) -> None:
    log_msg(f"Waiting for job {job_id} to get status {target_status}...")
    with timeout(timeout_s):
        status = get_job_status(job_id)
        if status == target_status:
            log_msg("Done.")
            return
        if status in JOB_STATUSES_TERMINATED:
            raise RuntimeError(f"Unexpected terminated job status: {job_id}, {status}")
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
