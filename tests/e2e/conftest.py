import os
import tempfile
import time
import typing as t
from collections import namedtuple
from pathlib import Path

import pytest

from tests.e2e.configuration import (
    CI,
    EXISTING_PROJECT_SLUG,
    FILE_SIZE_B,
    LOCAL_CLEANUP_SCRIPT_PATH,
    LOCAL_CLEANUP_STORAGE_FILE,
    LOCAL_PROJECT_CONFIG_PATH,
    LOCAL_ROOT_PATH,
    LOCAL_TESTS_SAMPLES_PATH,
    LOGGER_NAME,
    MK_CODE_DIR,
    MK_DATA_DIR,
    MK_NOTEBOOKS_DIR,
    MK_PROJECT_PATH_STORAGE,
    MK_PROJECT_SLUG,
    N_FILES,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PROJECT_APT_FILE_NAME,
    PROJECT_PIP_FILE_NAME,
    TIMEOUT_NEURO_LOGIN,
    UNIQUE_PROJECT_NAME,
)
from tests.e2e.helpers.logs import log_msg
from tests.e2e.helpers.runners import run
from tests.e2e.helpers.utils import copy_local_files, generate_random_file
from tests.utils import inside_dir


# == pytest config ==


def pytest_logger_config(logger_config: t.Any) -> None:
    """Pytest logging setup"""
    loggers = [LOGGER_NAME]
    logger_config.add_loggers(loggers, stdout_level="info")
    logger_config.set_log_option_default(",".join(loggers))


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
        environment = request.config.getoption("--environment") or "dev"
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
def change_directory_to_temp() -> t.Iterator[None]:
    tmp = os.path.join(tempfile.gettempdir(), "test-cookiecutter")
    os.makedirs(tmp, exist_ok=True)
    with inside_dir(tmp):
        yield


@pytest.fixture(scope="session", autouse=True)
def cookiecutter_setup(change_directory_to_temp: None) -> t.Iterator[None]:
    if not EXISTING_PROJECT_SLUG:
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
    if EXISTING_PROJECT_SLUG:
        return

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

    data_dir = Path(MK_DATA_DIR)
    log_msg(f"Generating data to `{data_dir}/`")
    assert data_dir.is_dir() and data_dir.exists()
    for _ in range(N_FILES):
        generate_random_file(data_dir, FILE_SIZE_B)
    assert len(list(data_dir.iterdir())) >= N_FILES

    code_dir = Path(MK_CODE_DIR)
    log_msg(f"Generating code files to `{code_dir}/`")
    assert code_dir.is_dir() and code_dir.exists()
    code_file = code_dir / "main.py"
    code_file.write_text("print('Hello world!')")
    assert code_file.exists()

    notebooks_dir = Path(MK_NOTEBOOKS_DIR)
    assert notebooks_dir.is_dir() and notebooks_dir.exists()
    copy_local_files(LOCAL_TESTS_SAMPLES_PATH, notebooks_dir)
    assert list(notebooks_dir.iterdir())

    # Save project directory on storage for further cleanup:
    LOCAL_CLEANUP_STORAGE_FILE.write_text(MK_PROJECT_PATH_STORAGE)


@pytest.fixture(scope="session", autouse=True)
def pip_install_neuromation(generate_empty_project: None) -> None:
    if not EXISTING_PROJECT_SLUG:
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
        if not CI:
            # On CI, we run this script as a separate CI step "when: always"
            run(
                f"bash -c {LOCAL_CLEANUP_SCRIPT_PATH.absolute()} jobs",
                detect_new_jobs=False,
                verbose=True,
            )
