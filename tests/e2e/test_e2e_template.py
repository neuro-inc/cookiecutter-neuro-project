from pathlib import Path
from typing import Any

import pytest

from tests.e2e.configuration import (
    AWS_KEY_FILE,
    EXISTING_PROJECT_SLUG,
    GCP_KEY_FILE,
    JOB_ID_PATTERN,
    JOB_STATUS_SUCCEEDED,
    MK_CODE_DIR,
    MK_CONFIG_DIR,
    MK_DEVELOP_JOB,
    MK_FILEBROWSER_JOB,
    MK_JUPYTER_JOB,
    MK_NOTEBOOKS_DIR,
    MK_PROJECT,
    MK_PROJECT_PATH_ENV,
    MK_PROJECT_PATH_STORAGE,
    MK_RESULTS_DIR,
    MK_SETUP_JOB,
    MK_TENSORBOARD_JOB,
    WANDB_KEY_FILE,
    _get_pattern_connected_ssh,
    _get_pattern_status_running,
    _get_pattern_status_succeeded_or_running,
    mk_train_job,
)
from tests.e2e.conftest import (
    STEP_DOWNLOAD,
    STEP_KILL,
    STEP_LOCAL,
    STEP_PRE_RUN,
    STEP_PRE_SETUP,
    STEP_RUN,
    STEP_SETUP,
    STEP_UPLOAD,
)
from tests.e2e.helpers.logs import log_msg
from tests.e2e.helpers.runners import (
    finalize,
    neuro_ls,
    parse_job_id,
    parse_job_url,
    parse_jobs_ids,
    repeat_until_success,
    run,
    wait_job_change_status_to,
)
from tests.e2e.helpers.utils import measure_time


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_help_works() -> None:
    out = run("make help")
    assert "setup" in out, f"not found in output: `{out}`"


@pytest.mark.run(order=STEP_LOCAL)
def test_make_setup_local() -> None:
    cmd = "make setup-local"
    run(
        cmd, detect_new_jobs=False,
    )


@pytest.mark.run(order=STEP_LOCAL)
def test_make_lint_local() -> None:
    cmd = "make lint-local"
    run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_LOCAL + 1)
def test_make_format_local() -> None:
    cmd = "make format-local"
    run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_setup_required() -> None:
    run(
        "make jupyter",
        expect_patterns=["Please run 'make setup' first"],
        assert_exit_code=False,
        check_default_errors=False,
    )


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_gcloud_check_auth_failure() -> None:
    key = Path(MK_CONFIG_DIR) / GCP_KEY_FILE
    if key.exists():
        key.unlink()  # key must not exist in this test

    make_cmd = "make gcloud-check-auth"
    run(
        make_cmd,
        expect_patterns=["ERROR: Not found Google Cloud service account key file"],
        assert_exit_code=False,
    )


@pytest.mark.run(order=STEP_PRE_SETUP + 1)
def test_make_gcloud_check_auth_success(
    decrypt_gcp_key: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("GCP_SECRET_FILE", GCP_KEY_FILE)

    key = Path(MK_CONFIG_DIR) / GCP_KEY_FILE
    assert key.exists(), f"{key.absolute()} must exist"

    make_cmd = "make gcloud-check-auth"
    run(
        make_cmd,
        expect_patterns=[
            "Google Cloud will be authenticated via service account key file"
        ],
        assert_exit_code=True,
    )


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_aws_check_auth_failure() -> None:
    key = Path(MK_CONFIG_DIR) / AWS_KEY_FILE
    if key.exists():
        key.unlink()  # key must not exist in this test

    make_cmd = "make aws-check-auth"
    run(
        make_cmd,
        expect_patterns=["ERROR: Not found AWS user account credentials file"],
        assert_exit_code=False,
    )


@pytest.mark.run(order=STEP_PRE_SETUP + 1)
def test_make_aws_check_auth_success(decrypt_aws_key: None, monkeypatch: Any) -> None:
    monkeypatch.setenv("AWS_SECRET_FILE", AWS_KEY_FILE)

    key = Path(MK_CONFIG_DIR) / AWS_KEY_FILE
    assert key.exists(), f"{key.absolute()} must exist"

    make_cmd = "make aws-check-auth"
    run(
        make_cmd,
        expect_patterns=["AWS will be authenticated via user account credentials file"],
        assert_exit_code=True,
    )


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_wandb_check_auth_failure() -> None:
    key = Path(MK_CONFIG_DIR) / WANDB_KEY_FILE
    if key.exists():
        key.unlink()  # key must not exist in this test

    make_cmd = "make wandb-check-auth"
    run(
        make_cmd,
        expect_patterns=["ERROR: Not found Weights & Biases key file"],
        assert_exit_code=False,
    )


@pytest.mark.run(order=STEP_PRE_SETUP + 1)
def test_make_wandb_check_auth_success(
    decrypt_wandb_key: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)

    key = Path(MK_CONFIG_DIR) / WANDB_KEY_FILE
    assert key.exists(), f"{key.absolute()} must exist"

    make_cmd = "make wandb-check-auth"
    run(
        make_cmd,
        expect_patterns=[r"Weights \& Biases will be authenticated via key file"],
        assert_exit_code=True,
    )


@pytest.mark.run(order=STEP_SETUP)
@pytest.mark.skipif(
    condition=EXISTING_PROJECT_SLUG is not None and len(EXISTING_PROJECT_SLUG) > 0,
    reason="Reusing existing project, no need to run setup",
)
def test_make_setup_full() -> None:
    try:
        with finalize(f"neuro kill {MK_SETUP_JOB}"):
            make_cmd = "make setup"
            with measure_time(make_cmd):
                run(
                    make_cmd,
                    expect_patterns=[_get_pattern_status_running(), JOB_ID_PATTERN],
                )
            run("make kill-setup", detect_new_jobs=False)
    except Exception:
        pytest.exit(f"Test on `make setup` failed, aborting the whole test suite.")
        raise


@pytest.mark.run(order=STEP_PRE_RUN)
def test_import_code_in_notebooks(
    env_var_preset_cpu_small: None, env_var_no_http_auth: None
) -> None:
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        assert "demo.ipynb" in neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
        assert "train.py" in neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")

        cmd = "make jupyter"
        nb_path = f"{MK_PROJECT_PATH_ENV}/{MK_NOTEBOOKS_DIR}/demo.ipynb"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=[_get_pattern_status_running()],
                error_patterns=[
                    fr"pattern '{nb_path}' matched no files",
                    "CellExecutionError",
                    "ModuleNotFoundError",
                ],
                assert_exit_code=False,
            )

        run(
            f'neuro exec --no-key-check --no-tty {MK_JUPYTER_JOB} "stat {nb_path}"',
            expect_patterns=[fr"File: {nb_path}"],
            detect_new_jobs=False,
        )

        expected_string = r"----\s+Your training script here\s+----"

        out_file = f"/tmp/out-nbconvert-{MK_PROJECT}"
        exec_cmd = (
            "bash -c 'jupyter nbconvert --execute --no-prompt --no-input "
            f"--to=asciidoc --output={out_file} {nb_path} && "
            f"cat {out_file}.asciidoc'"
        )
        cmd = f'neuro exec --no-key-check --no-tty {MK_JUPYTER_JOB} "{exec_cmd}"'
        run(
            cmd,
            expect_patterns=[fr"Writing \d+ bytes to {out_file}", expected_string],
            error_patterns=["Error: ", "CRITICAL"],
            detect_new_jobs=False,
        )

        cmd = "make kill-jupyter"
        with measure_time(cmd):
            run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_UPLOAD)
@pytest.mark.parametrize(
    "what", ["code", "data", "config", "notebooks", "results", "all"]
)
def test_make_upload(what: str) -> None:
    make_cmd = f"make upload-{what}"
    with measure_time(make_cmd):
        run(make_cmd)


@pytest.mark.run(order=STEP_DOWNLOAD)
@pytest.mark.parametrize(
    "what", ["code", "data", "config", "notebooks", "results", "all"]
)
def test_make_download(what: str) -> None:
    make_cmd = f"make download-{what}"
    with measure_time(make_cmd):
        run(make_cmd)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_defaults(env_var_preset_cpu_small: None) -> None:
    with finalize(f"neuro kill {mk_train_job()}"):
        out = run(
            "make train", expect_patterns=[_get_pattern_status_succeeded_or_running()],
        )
        job_id = parse_job_id(out)
        wait_job_change_status_to(job_id, JOB_STATUS_SUCCEEDED)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_custom_command(
    monkeypatch: Any, env_py_command_check_gpu: str
) -> None:
    py_cmd = env_py_command_check_gpu
    assert "'" not in py_cmd, f"py_cmd contains single quotes: `{py_cmd}`"
    assert '"' not in py_cmd, f"py_cmd contains double quotes: `{py_cmd}`"
    cmd = f'bash -c "sleep 5 && python -W ignore -c \\"{py_cmd}\\""'
    log_msg(f"Setting env var: TRAIN_CMD=`{cmd}`")
    monkeypatch.setenv("TRAIN_CMD", cmd)

    # NOTE: tensorflow outputs a lot of debug info even with `python -W ignore`.
    #  To disable this, export env var `TF_CPP_MIN_LOG_LEVEL=3`
    #  (note: currently, `make train` doesn't allow us to set custom env vars, see #227)
    with finalize(f"neuro kill {mk_train_job()}"):
        out = run(
            "make train", expect_patterns=[_get_pattern_status_succeeded_or_running()],
        )
        job_id = parse_job_id(out)
        wait_job_change_status_to(job_id, JOB_STATUS_SUCCEEDED)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_tqdm(env_var_preset_cpu_small: str, monkeypatch: Any) -> None:
    with finalize(f"neuro kill {mk_train_job()}"):
        cmd = (
            'python -c "import time, tqdm; '
            '[time.sleep(0.1) for _ in tqdm.tqdm(range(1000))]"'
        )
        assert "'" not in cmd, f"cmd contains single quotes: `{cmd}`"
        log_msg(f"Setting env var: TRAIN_CMD=`{cmd}`")
        monkeypatch.setenv("TRAIN_CMD", cmd)

        cmd = "make train"
        with measure_time(cmd):
            run(
                cmd,
                detect_new_jobs=True,
                expect_patterns=[
                    _get_pattern_status_running(),
                    r"Streaming logs of the job",
                    r"\d+%.*\d+/10000",
                ],
                error_patterns=["[Ee]rror"],
                assert_exit_code=False,
            )

        run("make kill-train", detect_new_jobs=False)


@pytest.mark.run(order=STEP_RUN)
def test_make_hypertrain(
    decrypt_wandb_key: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("WANDB_SECRET_FILE", WANDB_KEY_FILE)

    run(
        "make wandb-check-auth",
        expect_patterns=[r"Weights \& Biases will be authenticated via key file"],
    )

    # Print wandb status for debugging reasons
    run("wandb status")

    n = 1
    with finalize("make kill-hypertrain-all"):
        out = run(
            f"make hypertrain N_JOBS={n}",
            expect_patterns=(
                [_get_pattern_status_running()] * n
                + [f"Started {n} hyper-parameter search jobs"]
            ),
        )
        jobs = parse_jobs_ids(out, expect_num=n)
        run("make ps-hypertrain", expect_patterns=jobs)

        with finalize(*(f"neuro kill {job}" for job in jobs)):
            for job in jobs:
                run(
                    f"neuro logs {job}",
                    expect_patterns=[
                        "Successfully logged in to Weights",
                        "wandb: Starting wandb agent",
                        "Running runs:",
                        "Agent received command: run",
                        "Agent starting run with config:",
                        "Your training script here",
                    ],
                    error_patterns=[r"ERROR", r"Error while calling W&B API"],
                    assert_exit_code=False,  # do not wait till end
                )

            # just check exit-code:
            run("make kill-hypertrain-all", detect_new_jobs=False)
            run("make kill-train-all", detect_new_jobs=False)

    # Check results of hyper-parameter search on storage
    results = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_DIR}")
    assert any(name.startswith("sweep-") for name in results), f"actual: {results}"


@pytest.mark.run(order=STEP_RUN)
def test_make_run_jupyter_notebook(env_var_no_http_auth: None) -> None:
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        _test_run_something_useful("jupyter", "/tree")


@pytest.mark.run(order=STEP_RUN)
def test_make_jupyter_lab(env_var_no_http_auth: None,) -> None:
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        _test_run_something_useful("jupyter", "/lab")


@pytest.mark.run(order=STEP_RUN)
def test_make_tensorboard(env_var_no_http_auth: None) -> None:
    with finalize(f"neuro kill {MK_TENSORBOARD_JOB}"):
        _test_run_something_useful("tensorboard", "/")


@pytest.mark.run(order=STEP_RUN)
def test_make_filebrowser(env_var_no_http_auth: None) -> None:
    with finalize(f"neuro kill {MK_FILEBROWSER_JOB}"):
        _test_run_something_useful("filebrowser", "/files/requirements.txt")


def _test_run_something_useful(target: str, path: str) -> None:
    # Can't test web UI with HTTP auth
    make_cmd = f"make {target}"
    with measure_time(make_cmd):
        out = run(
            make_cmd,
            expect_patterns=[_get_pattern_status_running()],
            assert_exit_code=False,
        )
    job_id = parse_job_id(out)
    url = parse_job_url(out)

    cmd = "make ps"
    with measure_time(cmd):
        out = run(cmd, detect_new_jobs=False)
    assert job_id in out, f"Not found job '{job_id}' in neuro-ps output: '{out}'"

    repeat_until_success(
        f"curl --fail {url}{path}",
        job_id,
        expect_patterns=[r"<[^>]*html.*>"],
        error_patterns=["curl: .+"],
        verbose=False,
        assert_exit_code=False,
    )

    make_cmd = f"make kill-{target}"
    with measure_time(make_cmd):
        run(make_cmd)
    wait_job_change_status_to(job_id, JOB_STATUS_SUCCEEDED)


@pytest.mark.run(order=STEP_RUN)
def test_make_develop() -> None:
    with finalize(f"neuro kill {MK_DEVELOP_JOB}"):
        cmd = "make develop"
        with measure_time(cmd):
            run(
                cmd, expect_patterns=[_get_pattern_status_running()],
            )

    with finalize(f"neuro kill {MK_DEVELOP_JOB}"):
        cmd = "make develop"
        with measure_time(cmd):
            run(
                cmd, expect_patterns=[_get_pattern_status_running()],
            )

    cmd = "make connect-develop"
    with measure_time(cmd):
        run(
            cmd, expect_patterns=[_get_pattern_connected_ssh()], assert_exit_code=False,
        )

    cmd = "make logs-develop"
    with measure_time(cmd):
        run(
            cmd, expect_patterns=["Starting SSH server"], assert_exit_code=False,
        )

    cmd = "make port-forward-develop"
    with measure_time(cmd):
        run(
            cmd,
            expect_patterns=[r"Press \^C to stop forwarding"],
            assert_exit_code=False,
        )

    cmd = "make kill-develop"
    with measure_time(cmd):
        run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_KILL)
def test_make_ps_connect_kill_train(env_var_preset_cpu_small: None) -> None:
    with finalize(f"neuro kill {mk_train_job()}"):
        cmd = 'make train TRAIN_CMD="sleep 3h"'
        with measure_time(cmd):
            run(
                cmd,
                detect_new_jobs=True,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )

        cmd = "make connect-train"
        with measure_time(cmd):
            run(
                cmd,
                detect_new_jobs=False,
                expect_patterns=[_get_pattern_connected_ssh()],
                assert_exit_code=False,
            )

        cmd = "make ps-train-all"
        with measure_time(cmd):
            run(
                cmd, detect_new_jobs=False, expect_patterns=[mk_train_job()],
            )

        cmd = "make kill-train"
        with measure_time(cmd):
            run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_KILL)
def test_make_kill_all() -> None:
    cmd = f"make kill-all"
    with measure_time(cmd):
        run(cmd, detect_new_jobs=False)
