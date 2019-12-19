import pytest

import tests.e2e.helpers.runners
from tests.e2e.configuration import (
    MK_DEVELOP_JOB,
    MK_JUPYTER_JOB,
    MK_TRAINING_JOB,
    TIMEOUT_NEURO_EXEC,
    TIMEOUT_NEURO_RUN_CPU,
)
from tests.e2e.conftest import STEP_RUN
from tests.e2e.helpers.utils import measure_time


@pytest.mark.run(order=STEP_RUN)
def test_make_develop_connect_gsutil(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None
) -> None:
    _test_make_develop_connect_gsutil()


@tests.e2e.helpers.runners.try_except_finally(f"neuro kill {MK_DEVELOP_JOB}")
def _test_make_develop_connect_gsutil() -> None:
    cmd = "make develop"
    _test_make_run_job_connect_gsutil(cmd)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_connect_gsutil(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None
) -> None:
    _test_make_train_connect_gsutil()


@tests.e2e.helpers.runners.try_except_finally(f"neuro kill {MK_TRAINING_JOB}")
def _test_make_train_connect_gsutil() -> None:
    cmd = "make train  TRAINING_COMMAND='sleep 1h'"
    _test_make_run_job_connect_gsutil(cmd)


@pytest.mark.run(order=STEP_RUN)
def test_make_jupyter_connect_gsutil(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None
) -> None:
    _test_make_jupyter_connect_gsutil()


@tests.e2e.helpers.runners.try_except_finally(f"neuro kill {MK_JUPYTER_JOB}")
def _test_make_jupyter_connect_gsutil() -> None:
    cmd = "make jupyter"
    _test_make_run_job_connect_gsutil(cmd)


def _test_make_run_job_connect_gsutil(run_job_cmd: str) -> None:
    with measure_time(run_job_cmd):
        out = tests.e2e.helpers.runners.run(
            run_job_cmd,
            verbose=True,
            expect_patterns=[r"Status:[^\n]+running"],
            timeout_s=TIMEOUT_NEURO_RUN_CPU,
            assert_exit_code=False,
        )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

    bash_cmd = "gsutil cat gs://cookiecutter-e2e/hello.txt"
    cmd = f"neuro exec -T --no-key-check {job_id} '{bash_cmd}'"
    with measure_time(cmd):
        tests.e2e.helpers.runners.run(
            cmd,
            verbose=True,
            expect_patterns=["Hello world!"],
            timeout_s=TIMEOUT_NEURO_EXEC,
        )

    py_cmd_list = [
        "from google.cloud import storage",
        'bucket = storage.Client().get_bucket("cookiecutter-e2e")',
        'text = bucket.get_blob("hello.txt").download_as_string()',
        "print(text)",
        'assert "Hello world" in text.decode()',
    ]
    py_cmd = "; ".join(py_cmd_list)
    py_cmd = py_cmd.replace('"', r"\"")
    cmd = f"neuro exec -T --no-key-check {job_id} 'python -c \"{py_cmd}\"'"
    with measure_time(cmd):
        tests.e2e.helpers.runners.run(
            cmd,
            verbose=True,
            expect_patterns=["Hello world!"],
            error_patterns=["AssertionError"],
            timeout_s=TIMEOUT_NEURO_EXEC,
        )


@pytest.mark.run(order=STEP_RUN)
def test_make_develop_connect_wandb(
    generate_wandb_key: None, env_var_preset_cpu_small: None
) -> None:
    _test_make_develop_connect_wandb()


@tests.e2e.helpers.runners.try_except_finally(f"neuro kill {MK_DEVELOP_JOB}")
def _test_make_develop_connect_wandb() -> None:
    cmd = "make develop"
    _test_make_run_job_connect_wandb(cmd)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_connect_wandb(
    generate_wandb_key: None, env_var_preset_cpu_small: None
) -> None:
    _test_make_train_connect_wandb()


@tests.e2e.helpers.runners.try_except_finally(f"neuro kill {MK_TRAINING_JOB}")
def _test_make_train_connect_wandb() -> None:
    cmd = "make train  TRAINING_COMMAND='sleep 1h'"
    _test_make_run_job_connect_wandb(cmd)


@pytest.mark.run(order=STEP_RUN)
def test_make_jupyter_connect_wandb(
    generate_wandb_key: None, env_var_preset_cpu_small: None
) -> None:
    _test_make_jupyter_connect_wandb()


@tests.e2e.helpers.runners.try_except_finally(f"neuro kill {MK_JUPYTER_JOB}")
def _test_make_jupyter_connect_wandb() -> None:
    cmd = "make jupyter"
    _test_make_run_job_connect_wandb(cmd)


def _test_make_run_job_connect_wandb(run_job_cmd: str) -> None:
    with measure_time(run_job_cmd):
        out = tests.e2e.helpers.runners.run(
            run_job_cmd,
            verbose=True,
            expect_patterns=[r"Status:[^\n]+running"],
            timeout_s=TIMEOUT_NEURO_RUN_CPU,
            assert_exit_code=False,
        )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

    bash_cmd = 'bash -c "wandb status | grep -e "Logged in.* True""'
    cmd = f"neuro exec -T --no-key-check {job_id} '{bash_cmd}'"
    with measure_time(cmd):
        tests.e2e.helpers.runners.run(
            cmd, verbose=True, timeout_s=TIMEOUT_NEURO_EXEC, assert_exit_code=True
        )

    py_cmd_list = [
        "import wandb",
        "api = wandb.Api()",
        'runs = api.runs("art-em/cookiecutter-neuro-project")',
        "print(runs)",
    ]
    py_cmd = "; ".join(py_cmd_list)
    py_cmd = py_cmd.replace('"', r"\"")
    cmd = f"neuro exec -T --no-key-check {job_id} 'python -c \"{py_cmd}\"'"
    with measure_time(cmd):
        tests.e2e.helpers.runners.run(
            cmd,
            verbose=True,
            expect_patterns=["<Runs art-em/cookiecutter-neuro-project"],
            error_patterns=["TypeError", "Permission denied"],
            timeout_s=TIMEOUT_NEURO_EXEC,
        )
