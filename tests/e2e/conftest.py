import logging
import os
import re
import shlex
import shutil
import signal
import subprocess
import textwrap
import time
import typing as t
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path
from time import sleep
from uuid import uuid4

import pytest

from tests.utils import inside_dir


LOGGER_NAME = "e2e"
OUT_DIRECTORY_NAME = "out"
SUBMITTED_JOBS_FILE_NAME = "submitted_jobs.txt"


SHORT_TIMEOUT_SEC = 10
LONG_TIMEOUT_SEC = 10 * 60

# TODO: use a real dataset after cleaning up docs
FILE_SIZE_KB = 4
FILE_SIZE_B = FILE_SIZE_KB * 1024
N_FILES = 1000
PACKAGES_APT = ["vim", "nginx", "figlet"]
PACKAGES_PIP = ["aiohttp==3.5.4", "aiohttp_security==0.4.0", "neuromation"]

TIMEOUT_NEURO_LOGIN = 5
TIMEOUT_NEURO_JOB_RUN = 30
TIMEOUT_NEURO_UPLOAD = TIMEOUT_NEURO_DOWNLOAD = 40
TIMEOUT_NEURO_STORAGE_LS = 4
TIMEOUT_NEURO_STORAGE_RM = 10


VERBS_SECRET = ("login-with-token",)
VERBS_JOB_RUN = ("run", "submit")

SysCap = namedtuple("SysCap", "out err")
ESCAPE_LOG_CHARACTERS: t.Sequence[t.Tuple[str, str]] = [("\n", "\\n")]

ROOT_PATH = Path(__file__).resolve().parent.parent.parent
TESTS_ROOT_PATH = ROOT_PATH / "tests"
TESTS_SAMPLES_PATH = TESTS_ROOT_PATH / "samples"
COOKIECUTTER_CONFIG_PATH = TESTS_ROOT_PATH / "cookiecutter.yaml"
# Project name is defined in cookiecutter.yaml, from `project_name`
COOKIECUTTER_PROJECT_NAME = "test-project"

COOKIECUTTER_DATA_DIR_NAME = "data"
COOKIECUTTER_CODE_DIR_NAME = "modules"
COOKIECUTTER_NOTEBOOKS_DIR_NAME = "notebooks"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    return logger


log = get_logger()


def pytest_logger_config(logger_config: t.Any) -> None:
    """Pytest logging setup"""
    loggers = [LOGGER_NAME]
    logger_config.add_loggers(loggers, stdout_level="info")
    logger_config.set_log_option_default(",".join(loggers))


def get_submitted_jobs_file() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    out_path = project_root / OUT_DIRECTORY_NAME
    result_path = out_path / SUBMITTED_JOBS_FILE_NAME
    if not out_path.exists():
        out_path.mkdir(parents=True)
    log.info(f"Using jobs dump file: {result_path.absolute()}")
    return result_path


SUBMITTED_JOBS_FILE = get_submitted_jobs_file()


job_id_pattern = re.compile(
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
    run_once(
        f"cookiecutter --no-input --config-file={COOKIECUTTER_CONFIG_PATH} {ROOT_PATH}"
    )
    with inside_dir(COOKIECUTTER_PROJECT_NAME):
        yield


@pytest.fixture(scope="session", autouse=True)
def generate_empty_project(run_cookiecutter: None) -> None:
    log.info(f"Initializing empty project: {Path().absolute()}")

    apt_file = Path("apt.txt")
    assert apt_file.is_file() and apt_file.exists()
    with apt_file.open("a") as f:
        for package in PACKAGES_APT:
            f.write("\n" + package)

    pip_file = Path("requirements.txt")
    assert pip_file.is_file() and pip_file.exists()
    with pip_file.open("a") as f:
        for package in PACKAGES_PIP:
            f.write("\n" + package)

    data_dir = Path(COOKIECUTTER_DATA_DIR_NAME)
    assert data_dir.is_dir() and data_dir.exists()
    for _ in range(N_FILES):
        generate_random_file(data_dir, FILE_SIZE_B)
    assert len(list(data_dir.iterdir())) >= N_FILES

    code_dir = Path(COOKIECUTTER_CODE_DIR_NAME)
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

    notebooks_dir = Path(COOKIECUTTER_NOTEBOOKS_DIR_NAME)
    assert notebooks_dir.is_dir() and notebooks_dir.exists()
    copy_local_files("*.ipynb", from_dir=TESTS_SAMPLES_PATH, to_dir=notebooks_dir)
    assert list(notebooks_dir.iterdir())


@pytest.fixture(scope="session", autouse=True)
def pip_install_neuromation() -> None:
    captured = run_once("pip install -U neuromation")
    # stderr can contain: "You are using pip version..."
    patterns = (
        r"Requirement already up-to-date: .*neuromation",
        r"Successfully installed .*neuromation",
    )
    assert any(
        re.search(pattern, captured.out) for pattern in patterns
    ), f"stdout: `{captured.out}`"
    assert "Name: neuromation" in run_once("pip show neuromation").out


@pytest.fixture(scope="session", autouse=True)
def neuro_login(pip_install_neuromation: None) -> t.Iterator[None]:
    token = os.environ["COOKIECUTTER_TEST_E2E_TOKEN"]
    url = os.environ["COOKIECUTTER_TEST_E2E_URL"]
    try:
        captured = run_once(
            f"neuro config login-with-token {token} {url}",
            timeout_sec=TIMEOUT_NEURO_LOGIN,
        )
        assert f"Logged into {url}" in captured.out, f"stdout: `{captured.out}`"
        log.info(run_once("neuro config show").out)
        yield
    finally:
        nmrc = Path("~/.nmrc").expanduser()
        log.info(f"Deleting {nmrc} file")
        nmrc.unlink()
        log.info("Deleted")


# == helpers ==


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
def measure_time(operation_name: str = "") -> t.Iterator[None]:
    log.info("")
    start_time = time.time()
    yield
    elapsed_time = time.time() - start_time
    log.info(f"  TIME SUMMARY [{operation_name}]: {elapsed_time:.2f} sec")
    log.info("")


def run_detach_wait_substrings(
    cmd: str,
    *,
    log_stdout: bool = True,
    expect_stdouts: t.List[str],
    unexpect_stdouts: t.Sequence[str] = (),
) -> None:
    process = run_detach(cmd)
    log.info(f"Waiting for strings in stdout: {expect_stdouts}...")
    job_saved = False
    assert expect_stdouts
    expect_stdouts_iter = iter(expect_stdouts)
    current_expect_stdout = next(expect_stdouts_iter)
    for line in process.stdout:
        if log_stdout:
            log.info(f"stdout: `{_escape_log(line)}`")
        if not job_saved and _remember_job_runned(cmd, line):
            job_saved = True
        if current_expect_stdout in line:
            log.info(f"found in stdout: {current_expect_stdout}")
            try:
                current_expect_stdout = next(expect_stdouts_iter)
                log.info("waiting for the next string...")
            except StopIteration:
                log.info("returning")
                return
        for unexpect_stdout in unexpect_stdouts:
            if unexpect_stdout in line:
                raise RuntimeError(f"Found `{unexpect_stdout}` in stdout")

    log.error(f"COULD NOT FOIND STRING `{current_expect_stdout}` IN STDOUT")
    stderr = process.stderr.read()
    if stderr:
        log.error(f"STDERR: `{stderr}`")
    if process.returncode != 0:
        log.error(f"RETURN CODE: {process.returncode}")
    raise RuntimeError()


def run_detach(cmd: str) -> subprocess.Popen:
    args = shlex.split(cmd)
    if not any(verb in args for verb in VERBS_SECRET):
        log.info(f"Running detach: `{cmd}`")
    process = subprocess.Popen(
        args, encoding="utf8", stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return process


def run_repeatedly_wait_substring(cmd: str, *, expect_stdout: str) -> None:
    DELAY_SEC = 2
    captured: t.Optional[SysCap] = None
    log.info("Waiting for string in stdout...")
    try:
        while True:
            captured = run_once(cmd, timeout_sec=SHORT_TIMEOUT_SEC)
            log.info(f"stderr: `{_escape_log(captured.err)}`")
            log.info(f"stdout: `{_escape_log(captured.out)}`")
            if expect_stdout in captured.out:
                log.info("found in stdout.")
                return
            sleep(DELAY_SEC)
    except Exception:
        if captured:
            log.info(f"Last stderr: `{_escape_log(captured.err)}`")
            log.info(f"Last stdout: `{_escape_log(captured.out)}`")
        raise


def run_once(
    cmd: str, timeout_sec: int = LONG_TIMEOUT_SEC, assert_success: bool = True
) -> SysCap:
    args = shlex.split(cmd)
    if not any(verb in args for verb in VERBS_SECRET):
        log.info(f"Running [timeout={timeout_sec}]: `{cmd}`")
    proc = subprocess.run(
        args,
        timeout=timeout_sec,
        encoding="utf8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if assert_success:
        try:
            proc.check_returncode()
        except subprocess.CalledProcessError:
            log.error(f"stderr: `{_escape_log(proc.stderr)}`")
            log.error(f"stdout: `{_escape_log(proc.stdout)}`")
            raise
    out = proc.stdout.strip()
    err = proc.stderr.strip()
    _remember_job_runned(cmd, out)
    return SysCap(out, err)


def _remember_job_runned(cmd: str, stdout: str) -> bool:
    if any(start in cmd for start in VERBS_JOB_RUN):
        match = job_id_pattern.search(stdout)
        if match:
            job_id = match.group(1)
            log.info(f"Detected job-id: {job_id}")
            with SUBMITTED_JOBS_FILE.open("a") as f:
                f.write("\n" + job_id)
                return True
    return False


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


def cleanup_local_dirs(*dirs: Path) -> None:
    for d in dirs:
        log.info(f"Cleaning up local directory `{d}`")
        for f in d.iterdir():
            if f.is_file():
                f.unlink()


def copy_local_files(glob: str, from_dir: Path, to_dir: Path) -> None:
    for f in from_dir.glob(glob):
        if not f.is_file():
            continue
        shutil.copyfile(str(f), to_dir / f.name)


def _escape_log(s: str) -> str:
    return repr(s).strip("'")
