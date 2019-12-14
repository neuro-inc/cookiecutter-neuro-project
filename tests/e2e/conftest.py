import os
import tempfile
import time
import typing as t
from collections import namedtuple
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from tests.e2e.configuration import (
    EXISTING_PROJECT_SLUG,
    FILE_SIZE_B,
    GCP_KEY_FILE,
    LOCAL_CLEANUP_STORAGE_FILE,
    LOCAL_PROJECT_CONFIG_PATH,
    LOCAL_ROOT_PATH,
    LOCAL_TESTS_SAMPLES_PATH,
    LOGGER_NAME,
    MK_CODE_DIR,
    MK_CONFIG_DIR,
    MK_DATA_DIR,
    MK_NOTEBOOKS_DIR,
    MK_PROJECT_PATH_STORAGE,
    MK_PROJECT_SLUG,
    N_FILES,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PROJECT_APT_FILE_NAME,
    PROJECT_PIP_FILE_NAME,
    SECRET_FILE_ENC_PATTERN,
    TIMEOUT_NEURO_LOGIN,
    TIMEOUT_NEURO_RUN_CPU,
    TIMEOUT_NEURO_RUN_GPU,
    UNIQUE_PROJECT_NAME,
    WANDB_KEY_FILE,
)
from tests.e2e.helpers.logs import LOGGER, log_msg
from tests.e2e.helpers.runners import run
from tests.e2e.helpers.utils import copy_local_files, generate_random_file
from tests.utils import inside_dir


STEP_PRE_SETUP = 0
STEP_SETUP = 3
STEP_POST_SETUP = 7
STEP_UPLOAD = 10
STEP_DOWNLOAD = 20
STEP_RUN = 30
STEP_KILL = 90
STEP_CLEANUP = 100
STEP_LOCAL = 200

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
def environment(request: t.Any) -> str:
    env = request.config.getoption("--environment") or "dev"
    if env not in ["dev", "staging"]:
        raise ValueError(f"Invalid environment: {environment}")
    return env


@pytest.fixture(scope="session")
def client_setup_factory(environment: str) -> t.Callable[[], ClientConfig]:
    def _f() -> ClientConfig:
        if environment == "dev":
            env_name_token = "COOKIECUTTER_TEST_E2E_DEV_TOKEN"
            env_name_url = "COOKIECUTTER_TEST_E2E_DEV_URL"
        else:
            env_name_token = "COOKIECUTTER_TEST_E2E_STAGING_TOKEN"
            env_name_url = "COOKIECUTTER_TEST_E2E_STAGING_URL"
        return ClientConfig(
            token=os.environ[env_name_token], url=os.environ[env_name_url]
        )

    return _f


@pytest.fixture(scope="session")
def env_neuro_run_timeout(environment: str) -> int:
    if environment == "dev":
        return TIMEOUT_NEURO_RUN_CPU
    else:
        return TIMEOUT_NEURO_RUN_GPU


@pytest.fixture(scope="session")
def env_py_command_check_gpu(environment: str) -> str:
    # Note: this command is NOT allowed to use single quotes
    # as the whole command for 'neuro run' will be passed in single quotes
    pre_cmds = ["import os, torch, tensorflow"]

    gpu_assertions = ["tensorflow.test.is_gpu_available()", "torch.cuda.is_available()"]
    if environment == "dev":
        cmd = "; ".join(pre_cmds + [f"assert not {gpu}" for gpu in gpu_assertions])
    else:
        cmd = "; ".join(pre_cmds + [f"assert {gpu}" for gpu in gpu_assertions])
    return cmd


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

    config_dir = Path(MK_CONFIG_DIR)
    assert config_dir.is_dir() and config_dir.exists()
    config_file = config_dir / "test-config"
    log_msg(f"Generating `{config_file}`")
    with config_file.open("w") as f:
        f.write("[foo]\nkey=val\n")

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
    code_file.write_text('print("Hello world!")\n')
    assert code_file.exists()

    notebooks_dir = Path(MK_NOTEBOOKS_DIR)
    assert notebooks_dir.is_dir() and notebooks_dir.exists()
    copy_local_files(LOCAL_TESTS_SAMPLES_PATH / "notebooks", notebooks_dir)
    assert list(notebooks_dir.iterdir())

    # Save project directory on storage for further cleanup:
    LOCAL_CLEANUP_STORAGE_FILE.write_text(MK_PROJECT_PATH_STORAGE)


@pytest.fixture(scope="session", autouse=True)
def pip_install_neuromation(generate_empty_project: None) -> None:
    if not EXISTING_PROJECT_SLUG:
        run("pip install -U neuromation", verbose=False)
    log_msg(f"Using: {run('neuro --version', verbose=False)}")


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


@pytest.fixture()
def env_var_preset_cpu_small(monkeypatch: t.Any) -> None:
    monkeypatch.setenv("PRESET", "cpu-small")


@pytest.fixture()
def env_var_no_http_auth(monkeypatch: t.Any) -> None:
    monkeypatch.setenv("HTTP_AUTH", "--no-http-auth")


def _decrypt_file(file_enc: Path, output: Path) -> None:
    log_msg(f"Decrypting `{file_enc}` to `{output}`")
    assert file_enc.exists(), f"encrypted file does not exist: {file_enc}"
    with file_enc.open(mode="rb") as f_enc:
        with output.open(mode="wb") as f_dec:
            fernet = Fernet(os.environ["COOKIECUTTER_GCP_CONFIG_ENCRYPTION_KEY"])
            dec = fernet.decrypt(f_enc.read())
            assert "cookiecutter-e2e" in dec.decode(), "could not decrypt file"
            f_dec.write(dec)


def _decrypt_key(key_name: str) -> t.Iterator[None]:
    key = Path(MK_CONFIG_DIR) / key_name
    try:
        if not key.exists():
            key_enc_name = SECRET_FILE_ENC_PATTERN.format(key=key_name)
            key_enc = Path(LOCAL_TESTS_SAMPLES_PATH) / "config" / key_enc_name
            _decrypt_file(key_enc, key)
        yield
    finally:
        if key.exists():
            try:
                key.unlink()
            except Exception as e:
                log_msg(
                    f"Could not delete file {key.absolute()}: {e}", logger=LOGGER.warn
                )


@pytest.fixture(autouse=True)
def env_var_gcp_secret_file(monkeypatch: t.Any) -> None:
    monkeypatch.setenv("GCP_SECRET_FILE", GCP_KEY_FILE)


@pytest.fixture(autouse=True, scope="function")
def decrypt_gcp_key() -> t.Iterator[None]:
    yield from _decrypt_key(GCP_KEY_FILE)


@pytest.fixture(autouse=True)
def env_var_wandb_secret_file(monkeypatch: t.Any) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)


@pytest.fixture(autouse=True, scope="function")
def generate_wandb_key() -> t.Iterator[None]:
    yield from _decrypt_key(WANDB_KEY_FILE)
