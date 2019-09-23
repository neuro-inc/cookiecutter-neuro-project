import logging
import os
import re
import shutil
import signal
import sys
import textwrap
import time
import typing as t
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pexpect
import pytest

from tests.e2e.configuration import (
    MK_CODE_PATH,
    MK_DATA_PATH,
    MK_NOTEBOOKS_PATH,
    MK_PROJECT_NAME,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PROJECT_APT_FILE_NAME,
    PROJECT_PIP_FILE_NAME,
    TIMEOUT_NEURO_LOGIN,
)
from tests.utils import inside_dir


LOGGER_NAME = "e2e"

SUBMITTED_JOBS_FILE_NAME = "submitted_jobs.txt"
CLEANUP_JOBS_SCRIPT_NAME = "cleanup_jobs.py"


DEFAULT_TIMEOUT_SHORT = 10
DEFAULT_TIMEOUT_LONG = 10 * 60

# TODO: use a real dataset after cleaning up docs
FILE_SIZE_KB = 4
FILE_SIZE_B = FILE_SIZE_KB * 1024
N_FILES = 15


VERBS_SECRET = ("login-with-token",)
VERBS_JOB_RUN = ("run", "submit")

# OutCode = namedtuple("OutCode", "output code")
ESCAPE_LOG_CHARACTERS: t.Sequence[t.Tuple[str, str]] = [("\n", "\\n")]

# all variables prefixed "LOCAL_" store paths to file on your local machine
LOCAL_ROOT_PATH = Path(__file__).resolve().parent.parent.parent
LOCAL_TESTS_ROOT_PATH = LOCAL_ROOT_PATH / "tests"
LOCAL_PROJECT_CONFIG_PATH = LOCAL_TESTS_ROOT_PATH / "cookiecutter.yaml"
LOCAL_TESTS_E2E_ROOT_PATH = LOCAL_TESTS_ROOT_PATH / "e2e"
LOCAL_TESTS_SAMPLES_PATH = LOCAL_TESTS_E2E_ROOT_PATH / "samples"
LOCAL_TESTS_LOGS_PATH = LOCAL_TESTS_E2E_ROOT_PATH / "logs"

LOCAL_SUBMITTED_JOBS_FILE = LOCAL_ROOT_PATH / SUBMITTED_JOBS_FILE_NAME
LOCAL_SUBMITTED_JOBS_CLEANER_SCRIPT_PATH = LOCAL_ROOT_PATH / CLEANUP_JOBS_SCRIPT_NAME

# use `sys.stdout` to echo everything to standard output
# use `open('mylog.txt','wb')` to log to a file
# use `None` to disable logging to console
PEXPECT_DEBUG_OUTPUT_LOGFILE = sys.stdout if os.environ.get("CI") != "true" else None

# note: ERROR, being the most general error, must go the last
DEFAULT_NEURO_ERROR_PATTERNS = (
    r"404: Not Found",
    r"Status: failed",
    r"ERROR[^:]*:[^\n]*",
)
DEFAULT_MAKE_ERROR_PATTERNS = (r"Makefile:[^\n]*", r"recipe for target[^\n]*")
DEFAULT_ERROR_PATTERNS = DEFAULT_MAKE_ERROR_PATTERNS + DEFAULT_NEURO_ERROR_PATTERNS


PEXPECT_BUFFER_SIZE_BYTES = 50 * 1024


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    return logger


log = get_logger()


def pytest_logger_config(logger_config: t.Any) -> None:
    """Pytest logging setup"""
    loggers = [LOGGER_NAME]
    logger_config.add_loggers(loggers, stdout_level="info")
    logger_config.set_log_option_default(",".join(loggers))


JOB_ID_PATTERN = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"(job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)


# == fixtures ==


@pytest.fixture(scope="session", autouse=True)
def change_directory_to_temp(tmpdir_factory: t.Any) -> t.Iterator[None]:
    tmp = tmpdir_factory.mktemp("test-cookiecutter")
    with inside_dir(str(tmp)):
        yield


@pytest.fixture(scope="session", autouse=True)
def run_cookiecutter(change_directory_to_temp: None) -> t.Iterator[None]:
    run(
        f"cookiecutter --no-input "
        f"--config-file={LOCAL_PROJECT_CONFIG_PATH} {LOCAL_ROOT_PATH}",
        stop_patterns=["raise .*Exception"],
    )
    with inside_dir(MK_PROJECT_NAME):
        yield


@pytest.fixture(scope="session", autouse=True)
def generate_empty_project(run_cookiecutter: None) -> None:
    log.info(f"Initializing empty project: `{Path().absolute()}`")

    apt_file = Path(PROJECT_APT_FILE_NAME)
    log.info(f"Copying `{apt_file}`")
    assert apt_file.is_file() and apt_file.exists()
    with apt_file.open("a") as f:
        for package in PACKAGES_APT_CUSTOM:
            f.write("\n" + package)

    pip_file = Path(PROJECT_PIP_FILE_NAME)
    log.info(f"Copying `{pip_file}`")
    assert pip_file.is_file() and pip_file.exists()
    with pip_file.open("a") as f:
        for package in PACKAGES_PIP_CUSTOM:
            f.write("\n" + package)

    data_dir = Path(MK_DATA_PATH)
    log.info(f"Generating data to `{data_dir}/`")
    assert data_dir.is_dir() and data_dir.exists()
    for _ in range(N_FILES):
        generate_random_file(data_dir, FILE_SIZE_B)
    assert len(list(data_dir.iterdir())) >= N_FILES

    code_dir = Path(MK_CODE_PATH)
    log.info(f"Generating code files to `{code_dir}/`")
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
def pip_install_neuromation() -> None:
    run("pip install -U neuromation")
    assert "Name: neuromation" in run("pip show neuromation")


@pytest.fixture(scope="session", autouse=True)
def neuro_login(pip_install_neuromation: None) -> t.Iterator[None]:
    token = os.environ["COOKIECUTTER_TEST_E2E_TOKEN"]
    url = os.environ["COOKIECUTTER_TEST_E2E_URL"]
    try:
        captured = run(
            f"neuro config login-with-token {token} {url}",
            timeout_s=TIMEOUT_NEURO_LOGIN,
            debug=False,
        )
        assert f"Logged into {url}" in captured, f"stdout: `{captured}`"
        time.sleep(0.5)  # sometimes flakes  # TODO: remove this sleep
        log.info(run("neuro config show"))

        yield

    finally:
        run(
            f"python '{LOCAL_SUBMITTED_JOBS_CLEANER_SCRIPT_PATH.absolute()}'",
            debug=True,
            detect_new_jobs=False,
        )
        if os.environ.get("CI") == "true":
            nmrc = Path("~/.nmrc").expanduser()
            log.info(f"Deleting {nmrc} file")
            nmrc.unlink()
            log.info("Deleted")


# == generic helpers ==


def unique_label() -> str:
    return uuid4().hex[:8]


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
        log.error(f"TIMEOUT ERROR: {time_s}")
        raise
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


@contextmanager
def measure_time(command_name: str = "") -> t.Iterator[None]:
    log.info("-" * 50)
    start_time = time.time()
    yield
    elapsed_time = time.time() - start_time
    log.info("=" * 50)
    log.info(f"  TIME SUMMARY [{command_name}]: {elapsed_time:.2f} sec")
    log.info("=" * 50)


# == execution helpers ==


def repeat_until_success(
    cmd: str,
    timeout_total_s: int = DEFAULT_TIMEOUT_LONG,
    interval_s: float = 1,
    **kwargs: t.Any,
) -> str:
    if not any(verb in cmd for verb in VERBS_SECRET):
        log.info(f"Running command until success: `{cmd}`")
    with timeout(timeout_total_s):
        while True:
            try:
                return run(cmd, **kwargs)
            except RuntimeError:
                pass
            time.sleep(interval_s)


# TODO: Move this helper to a separate file to use it from outside
def run(
    cmd: str,
    *,
    debug: bool = False,
    detect_new_jobs: bool = True,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    expect_patterns: t.Sequence[str] = (),
    stop_patterns: t.Sequence[str] = (),  # ignore errors (and stderr) by default
) -> str:
    """
    This method runs a command `cmd` via `pexpect.spawn()`, and iteratively
    searches for patterns defined in `expect_patterns` *in their order*
    (normally, `pexpect.expect([pattern1, pattern2, ...])` won't search
    them in a specified order). Once it sees any pattern from `stop_patterns`,
    it aborts its execution with `RuntimeError`. If any pattern from `expect_patterns`
    wasn't found, also `RuntimeError` is raised.
        Note: if you want `debug=True` to work,
        set `PEXPECT_DEBUG_OUTPUT_LOGFILE=sys.output`
    >>> # Check expected-outputs:
    >>> s = run("bash -c 'echo 1; echo 2; echo 3'",
    ...          debug=False,
    ...          expect_patterns=['1', '2'])
    >>> s.split()
    ['1', '2', '3']
    >>> # Check expected-outputs:
    >>> try:
    ...     run("bash -c 'echo 1; echo 2; echo 3'",
    ...          debug=False,
    ...          expect_patterns=['1', '3'],
    ...          stop_patterns=['2'])
    ... except RuntimeError as e:
    ...     assert str(e) == "Found stop-pattern: re.compile('2', re.DOTALL)"
    >>> # Works with only stop-patterns:
    >>> try:
    ...     run("bash -c 'echo 1; echo 2; echo 3'",
    ...          debug=False,
    ...          stop_patterns=['2'])
    ... except RuntimeError as e:
    ...     assert str(e) == "Found stop-pattern: re.compile('2', re.DOTALL)"
    >>> # Pattern not found at all:
    >>> try:
    ...     run("bash -c 'echo 1; echo 2; echo 3'",
    ...          debug=False,
    ...          expect_patterns=['1', '2', '3', '4'])
    ... except RuntimeError as e:
    ...     assert str(e) == "Could not find pattern: `4`"
    """

    if not any(verb in cmd for verb in VERBS_SECRET):
        log.info(f"Running command: `{cmd}`")
    child = pexpect.spawn(
        cmd,
        timeout=timeout_s,
        logfile=PEXPECT_DEBUG_OUTPUT_LOGFILE if debug else None,
        maxread=PEXPECT_BUFFER_SIZE_BYTES,
        searchwindowsize=PEXPECT_BUFFER_SIZE_BYTES // 100,
        encoding="utf-8",
    )

    compile_flags = re.DOTALL
    if child.ignorecase:
        compile_flags = compile_flags | re.IGNORECASE
    stop_patterns_compiled = [re.compile(p, compile_flags) for p in stop_patterns]
    if stop_patterns:
        log.info(f"Stop-patterns: {stop_patterns}")

    output = ""
    try:
        for expected in expect_patterns:
            log.info(f"Waiting for pattern: `{expected}`")
            expected_p = re.compile(expected, compile_flags)
            try:
                child.expect_list([expected_p] + stop_patterns_compiled)
                log.info(f"Found: `{expected}`")
                chunk = _get_chunk(child)
                output += chunk
            except pexpect.EOF:
                raise RuntimeError(f"Could not find pattern: `{expected}`")

            _raise_if_contains_stop_pattern(chunk, stop_patterns_compiled)
        # read the rest:
        # child.wait()
        while True:
            # TODO: read huge chunk in chunks
            chunk = child.read()
            if not chunk:
                break
            output += chunk
            _raise_if_contains_stop_pattern(chunk, stop_patterns_compiled)

        return output

    except RuntimeError as e:
        log.error(str(e))
        log.error(f"Dump: `{repr(output)}`")
        raise

    finally:
        if detect_new_jobs:
            _dump_submitted_job_ids(_detect_job_ids(output))


def _get_chunk(child: pexpect.pty_spawn.spawn) -> str:
    chunk = child.before
    if isinstance(child.after, child.allowed_string_types):
        chunk += child.after
    return chunk


def _raise_if_contains_stop_pattern(
    chunk: str, stop_patterns_compiled: t.List[t.Pattern[str]]
) -> None:
    for stop_p in stop_patterns_compiled:
        if stop_p.search(chunk):
            raise RuntimeError(f"Found stop-pattern: {stop_p}")


def _detect_job_ids(stdout: str) -> t.Set[str]:
    return set(JOB_ID_PATTERN.findall(stdout))


def _dump_submitted_job_ids(jobs: t.Iterable[str]) -> None:
    if jobs:
        log.info(f"Dumped jobs: {jobs}")
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
        log.info(f"Cleaning up local directory `{d.absolute()}`")
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
            log.info(f"Target `{target.absolute()}` already exists")
            continue
        log.info(f"Copying file `{f}` to `{target.absolute()}`")
        shutil.copyfile(f, target, follow_symlinks=False)


# == neuro helpers ==


def neuro_ls(path: str, timeout: int, ignore_errors: bool = False) -> t.Set[str]:
    out = run(
        f"neuro ls {path}",
        timeout_s=timeout,
        debug=False,
        stop_patterns=[] if ignore_errors else list(DEFAULT_NEURO_ERROR_PATTERNS),
    )
    result = set(out.split())
    if ".gitkeep" in result:
        result.remove(".gitkeep")
    return result


def neuro_rm_dir(
    project_relative_path: str, timeout: int, ignore_errors: bool = False
) -> None:
    log.info(f"Deleting remote directory `{project_relative_path}`")
    run(
        f"neuro rm -r {project_relative_path}",
        timeout_s=timeout,
        debug=False,
        stop_patterns=[] if ignore_errors else list(DEFAULT_NEURO_ERROR_PATTERNS),
    )


def neuro_ps(timeout: int) -> t.Set[str]:
    out = run(
        f"neuro --quiet ps",
        timeout_s=timeout,
        debug=True,
        stop_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    return set(out.split())
