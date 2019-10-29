import os
import re
import sys
from pathlib import Path
from uuid import uuid4


CI = os.environ.get("CI") == "true"


def unique_label() -> str:
    return uuid4().hex[:8]


LOGGER_NAME = "e2e"

# == timeouts ==

DEFAULT_TIMEOUT_SHORT = 10
DEFAULT_TIMEOUT_LONG = 10 * 60

TIMEOUT_MAKE_SETUP = 6 * 60
TIMEOUT_MAKE_UPLOAD_CODE = 10
TIMEOUT_MAKE_CLEAN_CODE = 3
TIMEOUT_MAKE_UPLOAD_DATA = 500
TIMEOUT_MAKE_CLEAN_DATA = 50
TIMEOUT_MAKE_UPLOAD_NOTEBOOKS = TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS = 5
TIMEOUT_MAKE_CLEAN_NOTEBOOKS = 5

TIMEOUT_NEURO_LOGIN = 15
TIMEOUT_NEURO_RUN_CPU = 30
TIMEOUT_NEURO_RUN_GPU = 5 * 60
TIMEOUT_NEURO_RMDIR_CODE = 10
TIMEOUT_NEURO_RMDIR_DATA = 60
TIMEOUT_NEURO_RMDIR_NOTEBOOKS = 10
TIMEOUT_NEURO_LS = 10
TIMEOUT_NEURO_STATUS = 20
TIMEOUT_NEURO_KILL = 20

# == Makefile constants ==

# all variables prefixed "MK_" are taken in Makefile (without prefix)
# Project name is defined in cookiecutter.yaml, from `project_name`
UNIQUE_PROJECT_NAME = f"Test Project {unique_label()}"
MK_PROJECT_POSTFIX = UNIQUE_PROJECT_NAME.lower().replace(" ", "-")
MK_PROJECT_SLUG = MK_PROJECT_POSTFIX.replace("-", "_")

MK_CODE_PATH = "modules"
MK_DATA_PATH = "data"
MK_NOTEBOOKS_PATH = "notebooks"
MK_REQUIREMENTS_PATH = "requirements"
MK_RESULTS_PATH = "results"
MK_PROJECT_PATH_STORAGE = f"storage:{MK_PROJECT_SLUG}"
MK_CODE_PATH_STORAGE = f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_PATH}"
MK_DATA_PATH_STORAGE = f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_PATH}"
MK_NOTEBOOKS_PATH_STORAGE = f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_PATH}"
MK_REQUIREMENTS_PATH_STORAGE = f"{MK_PROJECT_PATH_STORAGE}/{MK_REQUIREMENTS_PATH}"
MK_RESULTS_PATH_STORAGE = f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_PATH}"

MK_PROJECT_PATH_ENV = f"/{MK_PROJECT_SLUG}"
MK_CODE_PATH_ENV = f"{MK_PROJECT_PATH_ENV}/{MK_CODE_PATH}"
MK_DATA_PATH_ENV = f"{MK_PROJECT_PATH_ENV}/{MK_DATA_PATH}"
MK_NOTEBOOKS_PATH_ENV = f"{MK_PROJECT_PATH_ENV}/{MK_NOTEBOOKS_PATH}"
MK_REQUIREMENTS_PATH_ENV = f"{MK_PROJECT_PATH_ENV}/{MK_REQUIREMENTS_PATH}"
MK_RESULTS_PATH_ENV = f"{MK_PROJECT_PATH_ENV}/{MK_RESULTS_PATH}"

MK_SETUP_NAME = f"setup-{MK_PROJECT_POSTFIX}"
MK_TRAINING_NAME = f"training-{MK_PROJECT_POSTFIX}"
MK_JUPYTER_NAME = f"jupyter-{MK_PROJECT_POSTFIX}"
MK_TENSORBOARD_NAME = f"tensorboard-{MK_PROJECT_POSTFIX}"
MK_FILEBROWSER_NAME = f"filebrowser-{MK_PROJECT_POSTFIX}"

# MK_BASE_ENV_NAME = "neuromation/base"
# MK_CUSTOM_ENV_NAME = f"image:neuromation-{MK_PROJECT_POSTFIX}"


PROJECT_APT_FILE_NAME = "apt.txt"
PROJECT_PIP_FILE_NAME = "requirements.txt"

# NOTE: order of these constants must be the same as in Makefile
MK_PROJECT_FILES = [PROJECT_PIP_FILE_NAME, PROJECT_APT_FILE_NAME, "setup.cfg"]

# note: apt package 'expect' requires user input during installation
PACKAGES_APT_CUSTOM = ["python", "expect", "figlet"]
PACKAGES_PIP_CUSTOM = ["aiohttp==3.6", "aiohttp_security", "neuromation==19.9.10"]

PROJECT_HIDDEN_FILES = {".gitkeep"}
PROJECT_CODE_DIR_CONTENT = {"__init__.py", "main.py"}
PROJECT_NOTEBOOKS_DIR_CONTENT = {"Untitled.ipynb", "00_notebook_tutorial.ipynb"}


# == tests constants ==

LOG_FILE_NAME = "e2e-output.log"
CLEANUP_JOBS_FILE_NAME = "cleanup_jobs.txt"
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
LOCAL_CLEANUP_JOBS_FILE = LOCAL_TESTS_OUTPUT_PATH / CLEANUP_JOBS_FILE_NAME
LOCAL_CLEANUP_STORAGE_FILE = LOCAL_TESTS_OUTPUT_PATH / CLEANUP_STORAGE_FILE_NAME
LOCAL_CLEANUP_SCRIPT_PATH = LOCAL_TESTS_E2E_ROOT_PATH / CLEANUP_SCRIPT_FILE_NAME

# == neuro constants ==

VERBS_SECRET = ("login-with-token",)
VERBS_JOB_RUN = ("run", "submit")
JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUSES_TERMINATED = (JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED)
JOB_ID_DECLARATION_PATTERN = re.compile(
    # pattern for UUID v4 taken here: https://stackoverflow.com/a/38191078
    r"Job ID.*: (job-[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",  # noqa: E501 line too long
    re.IGNORECASE,
)


# == pexpect config ==

PEXPECT_BUFFER_SIZE_BYTES = 50 * 1024
# use `sys.stdout` to echo everything to standard output
# use `open('mylog.txt','wb')` to log to a file
# use `None` to disable logging to console
PEXPECT_DEBUG_OUTPUT_LOGFILE = (
    open(LOCAL_TESTS_OUTPUT_PATH / LOG_FILE_NAME, "a") if CI else sys.stdout
)
# note: ERROR, being the most general error, must go the last
DEFAULT_NEURO_ERROR_PATTERNS = (
    "404: Not Found",
    r"Status:[^\n]+failed",
    r"ERROR[^:]*: .+",
)
DEFAULT_MAKE_ERROR_PATTERNS = ("Makefile:.+", "recipe for target .+ failed.+")
DEFAULT_ERROR_PATTERNS = DEFAULT_MAKE_ERROR_PATTERNS + DEFAULT_NEURO_ERROR_PATTERNS


def _pattern_copy_file_started(file_name: str) -> str:
    return f"Copy[^']+'file://.*{file_name}'"


def _pattern_copy_file_finished(file_name: str) -> str:
    return rf"'{file_name}' \d+B"
