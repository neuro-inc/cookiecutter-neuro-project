from typing import Any

import pytest

import tests.e2e.helpers.runners
from tests.e2e.configuration import (
    AWS_KEY_FILE,
    DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
    GCP_KEY_FILE,
    MK_JUPYTER_JOB,
    TIMEOUT_NEURO_EXEC,
    TIMEOUT_NEURO_RUN_CPU,
    WANDB_KEY_FILE,
    mk_train_job,
)
from tests.e2e.conftest import STEP_RUN
from tests.e2e.helpers.runners import finalize, run
from tests.e2e.helpers.utils import measure_time


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_make_train_connect_gsutil_from_cli(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("GCP_SECRET_FILE", GCP_KEY_FILE)
    make_cmd = "make jupyter"

    with finalize(f"neuro kill {mk_train_job()}"):

        with measure_time(make_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                make_cmd,
                verbose=True,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=2,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        bash_cmd = "gsutil cat gs://cookiecutter-e2e/hello.txt"
        cmd = f'neuro exec -T --no-key-check {job_id} "{bash_cmd}"'
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, verbose=True, expect_patterns=["Hello world!"])


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_make_train_connect_gsutil_from_python_api(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("GCP_SECRET_FILE", GCP_KEY_FILE)
    make_cmd = "make jupyter"

    with finalize(f"neuro kill {mk_train_job()}"):

        with measure_time(make_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                make_cmd,
                verbose=True,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=2,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

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
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(
                cmd,
                verbose=True,
                attempts=2,
                expect_patterns=["Hello world!"],
                error_patterns=["AssertionError"],
            )


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_make_jupyter_connect_aws(
    decrypt_aws_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("AWS_SECRET_FILE", AWS_KEY_FILE)
    run_job_cmd = "make jupyter"
    kill_job_cmd = f"neuro kill {MK_JUPYTER_JOB}"

    with finalize(kill_job_cmd):
        with measure_time(run_job_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                run_job_cmd,
                verbose=True,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=3,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        bash_cmd = "aws s3 cp s3://cookiecutter-e2e/hello.txt -"
        cmd = f"neuro exec -T --no-key-check {job_id} '{bash_cmd}'"
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, verbose=True, expect_patterns=["Hello world!"])


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_make_jupyter_connect_wandb_from_cli(
    decrypt_wandb_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)
    run_job_cmd = "make jupyter"
    kill_job_cmd = f"neuro kill {MK_JUPYTER_JOB}"

    with finalize(kill_job_cmd):
        with measure_time(run_job_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                run_job_cmd,
                verbose=True,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=3,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        bash_cmd = 'bash -c "wandb status | grep -e "Logged in.* True""'
        cmd = f"neuro exec -T --no-key-check {job_id} '{bash_cmd}'"
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, verbose=True, assert_exit_code=True)


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_make_jupyter_connect_wandb_from_python_api(
    decrypt_wandb_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)
    run_job_cmd = "make jupyter"
    kill_job_cmd = f"neuro kill {MK_JUPYTER_JOB}"

    with finalize(kill_job_cmd):
        with measure_time(run_job_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                run_job_cmd,
                verbose=True,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=3,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        py_cmd_list = [
            "import wandb",
            "api = wandb.Api()",
            'runs = api.runs("art-em/cookiecutter-neuro-project")',
            "print(runs)",
        ]
        py_cmd = "; ".join(py_cmd_list)
        py_cmd = py_cmd.replace('"', r"\"")
        cmd = f"neuro exec -T --no-key-check {job_id} 'python -c \"{py_cmd}\"'"
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(
                cmd,
                attempts=2,
                verbose=True,
                expect_patterns=["<Runs art-em/cookiecutter-neuro-project"],
                error_patterns=["TypeError", "Permission denied"],
            )
