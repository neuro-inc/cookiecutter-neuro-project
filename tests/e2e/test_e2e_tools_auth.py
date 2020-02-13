from typing import Any

import pytest

import tests.e2e.helpers.runners
from tests.e2e.configuration import (
    AWS_KEY_FILE,
    GCP_KEY_FILE,
    MK_JUPYTER_JOB,
    TIMEOUT_NEURO_EXEC,
    TIMEOUT_NEURO_RUN_CPU,
    WANDB_KEY_FILE,
    _get_pattern_status_running,
)
from tests.e2e.conftest import STEP_RUN
from tests.e2e.helpers.runners import finalize, run
from tests.e2e.helpers.utils import measure_time


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_gsutil_auth_from_cli(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("GCP_SECRET_FILE", GCP_KEY_FILE)
    make_cmd = "make jupyter"
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        with measure_time(make_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                make_cmd,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        bash_cmd = "gsutil cat gs://cookiecutter-e2e/hello.txt"
        cmd = f'neuro exec -T --no-key-check {job_id} "{bash_cmd}"'
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, expect_patterns=["Hello world!"])


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_gsutil_auth_from_python_api(
    decrypt_gcp_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("GCP_SECRET_FILE", GCP_KEY_FILE)
    make_cmd = "make jupyter"
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        with measure_time(make_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                make_cmd,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        py_cmd = "; ".join(
            [
                "from google.cloud import storage",
                'bucket = storage.Client().get_bucket("cookiecutter-e2e")',
                'print(bucket.get_blob("hello.txt").download_as_string())',
            ]
        ).replace('"', r'\\"')
        bash_cmd = f"python -c '{py_cmd}'"
        cmd = f'neuro exec -T --no-key-check {job_id} "{bash_cmd}"'
        from tests.e2e.helpers.logs import log_msg

        log_msg(f"CMD: `{cmd}`")
        log_msg(f"CMD repr: `{repr(cmd)}`")
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, expect_patterns=["Hello world!"])


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_aws_auth(
    decrypt_aws_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("AWS_SECRET_FILE", AWS_KEY_FILE)
    run_job_cmd = "make jupyter"
    kill_job_cmd = f"neuro kill {MK_JUPYTER_JOB}"

    with finalize(kill_job_cmd):
        with measure_time(run_job_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                run_job_cmd,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        bash_cmd = "aws s3 cp s3://cookiecutter-e2e/hello.txt -"
        cmd = f'neuro exec -T --no-key-check {job_id} "{bash_cmd}"'
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, expect_patterns=["Hello world!"])


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_wandb_auth_from_cli(
    decrypt_wandb_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)
    run_job_cmd = "make jupyter"
    kill_job_cmd = f"neuro kill {MK_JUPYTER_JOB}"

    with finalize(kill_job_cmd):
        with measure_time(run_job_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                run_job_cmd,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        bash_cmd = "bash -c 'wandb status | grep -e \"Logged in.* True\"'"
        cmd = f'neuro exec -T --no-key-check {job_id} "{bash_cmd}"'
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, verbose=True)


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_wandb_auth_from_python_api(
    decrypt_wandb_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)
    make_cmd = "make jupyter"
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        with measure_time(make_cmd, TIMEOUT_NEURO_RUN_CPU):
            out = run(
                make_cmd,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )
        job_id = tests.e2e.helpers.runners.parse_job_id(out)

        py_cmd = "; ".join(
            [
                "import wandb",
                "api = wandb.Api()",
                'runs = api.runs("art-em/cookiecutter-neuro-project")',
                "print(runs)",
            ]
        ).replace('"', r"\"")
        bash_cmd = f"python -c '{py_cmd}'"
        cmd = f'neuro exec -T --no-key-check {job_id} "{bash_cmd}"'
        with measure_time(cmd, TIMEOUT_NEURO_EXEC):
            run(cmd, attempts=2, verbose=True)
