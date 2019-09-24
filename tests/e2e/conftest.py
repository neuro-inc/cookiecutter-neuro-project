import os
import re
import shutil
import sys
import textwrap
import time
import typing as t
from collections import namedtuple
from pathlib import Path

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
    TIMEOUT_NEURO_LS,
    TIMEOUT_NEURO_STATUS,
    UNIQUE_PROJECT_NAME,
)
from tests.e2e.utils import LOGGER_NAME, get_logger, timeout, unique_label
from tests.utils import inside_dir


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

JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUSES_TERMINATED = (JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED)
# use `sys.stdout` to echo everything to standard output
# use `open('mylog.txt','wb')` to log to a file
# use `None` to disable logging to console
PEXPECT_DEBUG_OUTPUT_LOGFILE = sys.stdout if os.environ.get("CI") != "true" else None

# note: ERROR, being the most general error, must go the last
DEFAULT_NEURO_ERROR_PATTERNS = ("404: Not Found", "Status: failed", r"ERROR[^:]*: .+")
DEFAULT_MAKE_ERROR_PATTERNS = ("Makefile:.+", "recipe for target .+ failed.+")
DEFAULT_ERROR_PATTERNS = DEFAULT_MAKE_ERROR_PATTERNS + DEFAULT_NEURO_ERROR_PATTERNS


PEXPECT_BUFFER_SIZE_BYTES = 50 * 1024


log = get_logger()


def pytest_logger_config(logger_config: t.Any) -> None:
    """Pytest logging setup"""
    loggers = [LOGGER_NAME]
    logger_config.add_loggers(loggers, stdout_level="info")
    logger_config.set_log_option_default(",".join(loggers))


JOB_ID_DECLARATION_PATTERN = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"Job ID.*: (job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",  # noqa: E501 line too long
    re.IGNORECASE,
)

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
        environment = request.config.getoption("--environment")
        log.info(f"Found option `--environment={environment}`")
        if not environment or environment == "dev":
            env_name_token = "COOKIECUTTER_TEST_E2E_DEV_TOKEN"
            env_name_url = "COOKIECUTTER_TEST_E2E_DEV_URL"
        elif environment == "staging":
            env_name_token = "COOKIECUTTER_TEST_E2E_STAGING_TOKEN"
            env_name_url = "COOKIECUTTER_TEST_E2E_STAGING_URL"
        else:
            raise ValueError(f"invalid environment: {environment}")
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
def run_cookiecutter(change_directory_to_temp: None) -> t.Iterator[None]:
    run(
        f"cookiecutter --no-input --config-file={LOCAL_PROJECT_CONFIG_PATH} "
        f'{LOCAL_ROOT_PATH} project_name="{UNIQUE_PROJECT_NAME}"',
        error_patterns=["raise .*Exception"],
        verbose=False,
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
    run("pip install -U neuromation", verbose=False)
    assert "Name: neuromation" in run("pip show neuromation", verbose=False)


@pytest.fixture(scope="session", autouse=True)
def neuro_login(pip_install_neuromation: None, client_setup_factory: t.Callable[[], ClientConfig]) -> None:
    config = client_setup_factory()
    captured = run(
        f"neuro config login-with-token {config.token} {config.url}",
        timeout_s=TIMEOUT_NEURO_LOGIN,
        verbose=False,
    )
    assert f"Logged into {config.url}" in captured, f"stdout: `{captured}`"
    time.sleep(0.5)  # sometimes flakes  # TODO: remove this sleep
    log.info(run("neuro config show", verbose=False))


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


# TODO: Move these helpers to a separate file to use it from outside


def run(
    cmd: str,
    *,
    expect_patterns: t.Sequence[str] = (),
    error_patterns: t.Sequence[str] = DEFAULT_ERROR_PATTERNS,
    verbose: bool = True,
    **kwargs: t.Any,
) -> str:
    """
    This method wraps method `run_once` and accepts all its named arguments.
    Once the command `cmd` is finished to be executed, the output is tested
    against the set of error patterns `error_patterns`, and if any of them
    was found, a `RuntimeError` will be raised.
    """
    out = run_once(cmd, expect_patterns, verbose=verbose, **kwargs)
    errors = detect_errors(out, error_patterns, verbose=verbose)
    if errors:
        raise RuntimeError(f"Detected errors in output: {repr(errors)}")
    return out


def run_once(
    cmd: str,
    expect_patterns: t.Sequence[str] = (),
    *,
    verbose: bool = True,
    detect_new_jobs: bool = True,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
) -> str:
    r"""
    This method runs a command `cmd` via `pexpect.spawn()`, and iteratively
    searches for patterns defined in `expect_patterns` *in their order*
    (normally, `pexpect.expect([pattern1, pattern2, ...])` won't search
    them in a specified order). If any expected pattern was not found,
    `RuntimeError` is raised. Use `verbose=True` to print useful information
    to log (also to dump all child process' output to the handler defined
    in `PEXPECT_DEBUG_OUTPUT_LOGFILE`).
    >>> # Check expected-outputs:
    >>> run("echo 1 2 3", expect_patterns=['1', '3'], verbose=False)
    '1 2 3\r\n'
    >>> # Empty pattern list:
    >>> run('echo 1 2 3', expect_patterns=[], verbose=False)
    '1 2 3\r\n'
    >>> # Pattern not found at all:
    >>> try:
    ...     run('echo 1 2 3', expect_patterns=['4'], verbose=False)
    ...     assert False, "must be unreachable"
    ... except RuntimeError as e:
    ...     assert str(e) == "NOT FOUND PATTERN: '4'", repr(str(e))
    """

    if verbose and not any(verb in cmd for verb in VERBS_SECRET):
        log.info(f"Running command: `{cmd}`")
    child = pexpect.spawn(
        cmd,
        timeout=timeout_s,
        logfile=PEXPECT_DEBUG_OUTPUT_LOGFILE if verbose else None,
        maxread=PEXPECT_BUFFER_SIZE_BYTES,
        searchwindowsize=PEXPECT_BUFFER_SIZE_BYTES // 100,
        encoding="utf-8",
    )
    output = ""
    need_dump = False
    if verbose and expect_patterns:
        log.info(f"Search patterns: {repr(expect_patterns)}")
    try:
        for expected in expect_patterns:
            try:
                child.expect(expected)
                if verbose:
                    log.info(f"Found pattern: {repr(expected)}")
            except pexpect.EOF:
                need_dump = True
                err = f"NOT FOUND PATTERN: {repr(expected)}"
                if verbose:
                    log.error(err)
                raise RuntimeError(err)
            finally:
                chunk = _get_chunk(child)
                output += chunk
    finally:
        output += _read_till_end(child)
        if detect_new_jobs:
            _dump_submitted_job_ids(_detect_job_ids(output))
        if verbose and need_dump:
            log.info(f"DUMP: {repr(output)}")
    return output


def _get_chunk(child: pexpect.pty_spawn.spawn) -> str:
    chunk = child.before
    if isinstance(child.after, child.allowed_string_types):
        chunk += child.after
    return chunk


def _read_till_end(child: pexpect.spawn) -> str:
    r"""
    >>> # _read_till_end() from the beginning:
    >>> child = pexpect.spawn("echo 1 2 3", encoding="utf8")
    >>> _read_till_end(child)
    '1 2 3\r\n'
    >>> _read_till_end(child)  # eof reached
    ''
    >>> _read_till_end(child)  # once again
    ''
    >>> # expect() and then _read_till_end():
    >>> child = pexpect.spawn("echo 1 2 3", encoding="utf8")
    >>> child.expect('2')
    0
    >>> _read_till_end(child)
    ' 3\r\n'
    >>> _read_till_end(child)  # eof reached
    ''
    """
    # read the rest:
    output = ""
    while True:
        # TODO: read in fixed-size chunks
        chunk = child.read()
        if not chunk:
            break
        output += chunk
    return output


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
                    log.info(f"Detected error matching {repr(p)}: {repr(err)}")
    if verbose and found:
        log.info(f"Overall {len(found)} patterns matched")
        log.info(f"DUMP: {repr(output)}")
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


def neuro_ls(path: str) -> t.Set[str]:
    out = run(
        f"neuro ls {path}",
        timeout_s=TIMEOUT_NEURO_LS,
        verbose=False,
        error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
    )
    result = set(out.split())
    if ".gitkeep" in result:
        result.remove(".gitkeep")
    return result


def neuro_rm_dir(
    project_relative_path: str, timeout_s: int, ignore_errors: bool = False
) -> None:
    log.info(f"Deleting remote directory `{project_relative_path}`")
    run(
        f"neuro rm -r {project_relative_path}",
        timeout_s=timeout_s,
        verbose=False,
        error_patterns=[] if ignore_errors else list(DEFAULT_NEURO_ERROR_PATTERNS),
    )


def wait_job_change_status_to(
    job_id: str,
    target_status: str,
    timeout_s: int = DEFAULT_TIMEOUT_LONG,
    delay_s: int = 1,
) -> None:
    log.info(f"Waiting for job {job_id} to get status {target_status}...")
    with timeout(timeout_s):
        out = run(
            f"neuro status {job_id}",
            timeout_s=TIMEOUT_NEURO_STATUS,
            verbose=False,
            error_patterns=DEFAULT_NEURO_ERROR_PATTERNS,
        )
        search = re.search(r"Status: (\w+)", out)
        assert search, f"not found job status in output: `{out}`"
        status = search.group(1)
        if status == target_status:
            return
        if status in JOB_STATUSES_TERMINATED:
            raise RuntimeError(f"Unexpected terminated job status: {job_id}, {status}")
        time.sleep(delay_s)
