import os
import re
from pathlib import Path
from uuid import uuid4


CI = os.environ.get("CI") == "true"


def unique_label() -> str:
    return uuid4().hex[:8]


LOGGER_NAME = "e2e"

# == timeouts ==

DEFAULT_TIMEOUT_SHORT = 3 * 10
DEFAULT_TIMEOUT_LONG = 3 * 60

# == Makefile constants ==

# all variables prefixed "MK_" are taken in Makefile (without prefix)
# Project name is defined in cookiecutter.yaml, from `project_name`
_unique_label = unique_label()
UNIQUE_PROJECT_NAME = f"Test Project {_unique_label}"
EXISTING_PROJECT_SLUG = os.environ.get("PROJECT")
MK_PROJECT = EXISTING_PROJECT_SLUG or UNIQUE_PROJECT_NAME.lower().replace(" ", "_")

MK_CODE_DIR = "modules"
MK_CONFIG_DIR = "config"
MK_DATA_DIR = "data"
MK_NOTEBOOKS_DIR = "notebooks"
MK_RESULTS_DIR = "results"

MK_PROJECT_PATH_STORAGE = f"storage:{MK_PROJECT}"
MK_PROJECT_PATH_ENV = "/project"


MK_BASE_ENV_NAME = "neuromation/base"
MK_CUSTOM_ENV_NAME = f"image:cookiecutter-e2e:{_unique_label}"


PROJECT_APT_FILE_NAME = "apt.txt"
PROJECT_PIP_FILE_NAME = "requirements.txt"

MK_PROJECT_DIRS = {
    MK_DATA_DIR,
    MK_CODE_DIR,
    MK_CONFIG_DIR,
    MK_NOTEBOOKS_DIR,
    MK_RESULTS_DIR,
}
# NOTE: order of these constants must be the same as in Makefile
MK_PROJECT_FILES = [PROJECT_PIP_FILE_NAME, PROJECT_APT_FILE_NAME, "setup.cfg"]

# note: apt package 'expect' requires user input during installation
PACKAGES_APT_CUSTOM = ["figlet"]
PACKAGES_PIP_CUSTOM = ["pexpect"]
GCP_KEY_FILE = "gcp-key.json"
SECRET_FILE_ENC_PATTERN = "{key}.enc"

PROJECT_CODE_DIR_CONTENT = {"__init__.py", "train.py"}
PROJECT_CONFIG_DIR_CONTENT = {
    "test-config",
    GCP_KEY_FILE,
}
PROJECT_NOTEBOOKS_DIR_CONTENT = {
    "demo.ipynb",
    "00_notebook_tutorial.ipynb",
}
PROJECT_RESULTS_DIR_CONTENT = {
    "sample.log",
}


# == tests constants ==

LOG_FILE_NAME = f"output_{MK_PROJECT}.log"
CLEANUP_STORAGE_FILE_NAME = "cleanup_storage.txt"
CLEANUP_SCRIPT_FILE_NAME = "cleanup.sh"

# TODO: use a real dataset after cleaning up docs
FILE_SIZE_KB = 4
FILE_SIZE_B = FILE_SIZE_KB * 1024
N_FILES = 15

# all variables prefixed "LOCAL_" store paths to file on your local machine
LOCAL_ROOT_PATH = Path(__file__).resolve().parent.parent.parent
LOCAL_TESTS_ROOT_PATH = LOCAL_ROOT_PATH / "tests"
LOCAL_PROJECT_CONFIG_PATH = LOCAL_TESTS_ROOT_PATH / "cookiecutter.yaml"
LOCAL_TESTS_E2E_ROOT_PATH = LOCAL_TESTS_ROOT_PATH / "e2e"
LOCAL_TESTS_SAMPLES_PATH = LOCAL_TESTS_E2E_ROOT_PATH / "samples"
LOCAL_TESTS_OUTPUT_PATH = LOCAL_TESTS_E2E_ROOT_PATH / "output"
LOCAL_TESTS_OUTPUT_PATH.mkdir(exist_ok=True)
LOCAL_CLEANUP_STORAGE_FILE = LOCAL_TESTS_OUTPUT_PATH / CLEANUP_STORAGE_FILE_NAME
LOCAL_CLEANUP_SCRIPT_PATH = LOCAL_TESTS_E2E_ROOT_PATH / CLEANUP_SCRIPT_FILE_NAME

# == neuro constants ==

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


# == pexpect config ==

PEXPECT_BUFFER_SIZE_BYTES = 10 * 1024 * 1024
# use `sys.stdout` to echo everything to standard output
# use `open('mylog.txt','wb')` to log to a file
# use `None` to disable logging to console
LOGFILE_PATH: Path = LOCAL_TESTS_OUTPUT_PATH / LOG_FILE_NAME
# note: ERROR, being the most general error, should go the last
DEFAULT_NEURO_ERROR_PATTERNS = (
    r"Status:[^\n]+failed",
    r"ERROR[^:]*: .+",
    r"Error: .+",
    r"Docker API error: .+",
    r"connection reset by peer",
)
DEFAULT_MAKE_ERROR_PATTERNS = ("recipe for target .+ failed.+",)
DEFAULT_ERROR_PATTERNS = DEFAULT_MAKE_ERROR_PATTERNS + DEFAULT_NEURO_ERROR_PATTERNS


def _pattern_copy_file_started(file_name: str) -> str:
    return f"Copy[^']+'file://.*{file_name}'"


def _pattern_copy_file_finished(file_name: str) -> str:
    return rf"'{file_name}' \d+B"


def _get_pattern_connected_ssh() -> str:
    return rf"root@{JOB_ID_PATTERN}"


def _get_pattern_status_running() -> str:
    return r"Status:[^\n]+running"


def _get_pattern_status_succeeded_or_running() -> str:
    return r"Status:[^\n]+(succeeded|running)"


def _get_pattern_pip_installing(pip: str) -> str:
    return fr"(Collecting|Requirement already satisfied)[^\n]*{pip}"
