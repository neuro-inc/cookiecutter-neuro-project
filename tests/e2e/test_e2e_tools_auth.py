import textwrap
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.configuration import (
    AWS_KEY_FILE,
    GCP_KEY_FILE,
    MK_CODE_DIR,
    MK_JUPYTER_JOB,
    TIMEOUT_NEURO_EXEC,
    TIMEOUT_NEURO_RUN_CPU,
    WANDB_KEY_FILE,
    _get_pattern_status_running,
    mk_train_job,
)
from tests.e2e.conftest import STEP_RUN
from tests.e2e.helpers.runners import finalize, parse_job_id, run
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
        job_id = parse_job_id(out)

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

    script_path = f"{MK_CODE_DIR}/check_gsutil.py"
    script = Path(script_path)
    script.write_text(
        textwrap.dedent(
            """
            from google.cloud import storage
            bucket = storage.Client().get_bucket("cookiecutter-e2e")
            print(bucket.get_blob("hello.txt").download_as_string())
            """
        )
    )
    make_cmd = "make upload-code"
    with measure_time(make_cmd):
        run(make_cmd, detect_new_jobs=False)

    make_cmd = f'make train TRAIN_CMD="python {script_path}" TRAIN_STREAM_LOGS=no'
    with finalize(f"neuro kill {mk_train_job()}"):
        with measure_time(make_cmd):
            out = run(make_cmd)

        job_id = parse_job_id(out)

        cmd = f"neuro logs {job_id}"
        with measure_time(cmd):
            run(
                cmd,
                attempts=2,
                expect_patterns=["Hello world!"],
                error_patterns=["Errno", "No such file or directory"],
            )


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
        job_id = parse_job_id(out)

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

    make_cmd = (
        "make train "
        "TRAIN_CMD=\"wandb status | grep -e 'Logged in.* True'\" "
        "TRAIN_STREAM_LOGS=no"
    )
    with finalize(f"neuro kill {mk_train_job()}"):
        with measure_time(make_cmd):
            run(make_cmd)


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
def test_wandb_auth_from_python_api(
    decrypt_wandb_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)

    script_path = f"{MK_CODE_DIR}/check_wandb.py"
    script = Path(script_path)
    script.write_text(
        textwrap.dedent(
            """
            import wandb
            api = wandb.Api()
            print(api.runs("art-em/cookiecutter-neuro-project"))
            """
        )
    )
    make_cmd = "make upload-code"
    with measure_time(make_cmd):
        run(make_cmd, detect_new_jobs=False)

    make_cmd = f'make train TRAIN_CMD="python {script_path}" TRAIN_STREAM_LOGS=no'
    with finalize(f"neuro kill {mk_train_job()}"):
        with measure_time(make_cmd):
            out = run(make_cmd)

        job_id = parse_job_id(out)

        cmd = f"neuro logs {job_id}"
        with measure_time(cmd):
            run(
                cmd,
                attempts=2,
                expect_patterns=["<Runs art-em/cookiecutter-neuro-project"],
                error_patterns=["TypeError", "Permission denied"],
            )
