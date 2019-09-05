import inspect
import logging
import re
import shlex
import signal
import subprocess
import typing as t
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path
from time import sleep
from uuid import uuid4


OUT_DIRECTORY_NAME = "out"
SUBMITTED_JOBS_FILE_NAME = "submitted_jobs.txt"

DEFAULT_TIMEOUT = 5 * 60

SysCap = namedtuple("SysCap", "out err")


job_id_pattern = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"(job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def get_submitted_jobs_file() -> Path:
    project_root = Path(__file__).resolve().parent
    out_path = project_root / OUT_DIRECTORY_NAME
    return out_path / SUBMITTED_JOBS_FILE_NAME


SUBMITTED_JOBS_FILE = get_submitted_jobs_file()

log = logging.getLogger(__name__)


def split_command(cmd: str) -> t.List[str]:
    return shlex.split(cmd)

def random_str(length: int) -> str:
    assert 0 <= length <= 32, length
    return uuid4().hex[:length]


def generate_job_name() -> str:
    postfix = f"-{random_str(4)}"
    return inspect.stack()[1].function.replace("_", "-") + postfix


@contextmanager
def timeout(time_s: int) -> t.Iterator[None]:
    """ source: https://www.jujens.eu/posts/en/2018/Jun/02/python-timeout-function/
    """

    def raise_timeout() -> t.NoReturn:
        raise TimeoutError

    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)  # type: ignore
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time_s)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def fire_and_forget(cmd: str) -> subprocess.Popen:
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    return proc


def wait_for_output(
    cmd: str, expect_stdin: str, timeout_s: int = DEFAULT_TIMEOUT
) -> None:
    delay_s = 1
    with timeout(timeout_s):
        while True:
            try:
                captured = run(cmd, timeout_s=timeout_s // 5)
                if captured.err:
                    print(f"stderr: `{captured.err}`")
            except subprocess.CalledProcessError as e:
                log.error(f"Caught error: {e}, retrying")
                continue
            if expect_stdin in captured.out:
                return
            sleep(delay_s)


def run(cmd: str, timeout_s: int = DEFAULT_TIMEOUT) -> SysCap:
    log.info(f"Runing command: '{cmd}'")
    print(f"Runing command: '{cmd}'")  # TODO : debug <--
    args = shlex.split(cmd)
    proc = subprocess.run(
        args,
        timeout=timeout_s,
        encoding="utf8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        proc.check_returncode()
    except subprocess.CalledProcessError:
        log.error(f"Last stdout: '{proc.stdout}'")
        log.error(f"Last stderr: '{proc.stderr}'")
        raise
    out = proc.stdout
    err = proc.stderr
    if any(start in " ".join(args) for start in ("submit", "run")):
        match = job_id_pattern.search(out)
        if match:
            job_id = match.group(1)
            with SUBMITTED_JOBS_FILE.open("a") as f:
                f.write(job_id + "\n")
    out = out.strip()
    err = err.strip()
    return SysCap(out, err)
