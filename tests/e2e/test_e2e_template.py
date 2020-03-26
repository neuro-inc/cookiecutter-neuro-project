# import sys
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.configuration import (
    AWS_KEY_FILE,
    DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
    EXISTING_PROJECT_SLUG,
    GCP_KEY_FILE,
    JOB_ID_PATTERN,
    JOB_STATUS_SUCCEEDED,
    MK_CODE_DIR,
    MK_CONFIG_DIR,
    MK_DATA_DIR,
    MK_DEVELOP_JOB,
    MK_FILEBROWSER_JOB,
    MK_JUPYTER_JOB,
    MK_NOTEBOOKS_DIR,
    MK_PROJECT,
    MK_PROJECT_FILES,
    MK_PROJECT_PATH_ENV,
    MK_PROJECT_PATH_STORAGE,
    MK_RESULTS_DIR,
    MK_RUN_DEFAULT,
    MK_SETUP_JOB,
    MK_TENSORBOARD_JOB,
    N_FILES,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PROJECT_CODE_DIR_CONTENT,
    PROJECT_CONFIG_DIR_CONTENT,
    PROJECT_NOTEBOOKS_DIR_CONTENT,
    PROJECT_RESULTS_DIR_CONTENT,
    TIMEOUT_MAKE_CLEAN_DATA,
    TIMEOUT_MAKE_CLEAN_NOTEBOOKS,
    TIMEOUT_MAKE_CLEAN_RESULTS,
    TIMEOUT_MAKE_DOWNLOAD_CONFIG,
    TIMEOUT_MAKE_DOWNLOAD_DATA,
    TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS,
    TIMEOUT_MAKE_DOWNLOAD_RESULTS,
    TIMEOUT_MAKE_SETUP,
    TIMEOUT_MAKE_UPLOAD_CODE,
    TIMEOUT_MAKE_UPLOAD_CONFIG,
    TIMEOUT_MAKE_UPLOAD_DATA,
    TIMEOUT_MAKE_UPLOAD_NOTEBOOKS,
    TIMEOUT_MAKE_UPLOAD_RESULTS,
    TIMEOUT_NEURO_EXEC,
    TIMEOUT_NEURO_KILL,
    TIMEOUT_NEURO_LOGS,
    TIMEOUT_NEURO_PORT_FORWARD,
    TIMEOUT_NEURO_RMDIR_CODE,
    TIMEOUT_NEURO_RMDIR_CONFIG,
    TIMEOUT_NEURO_RMDIR_DATA,
    TIMEOUT_NEURO_RMDIR_NOTEBOOKS,
    TIMEOUT_NEURO_RUN_CPU,
    TIMEOUT_NEURO_RUN_GPU,
    WANDB_KEY_FILE,
    _get_pattern_connected_ssh,
    _get_pattern_pip_installing,
    _get_pattern_status_running,
    _get_pattern_status_succeeded_or_running,
    _pattern_copy_file_finished,
    _pattern_copy_file_started,
    mk_train_job,
)
from tests.e2e.conftest import (
    STEP_CLEANUP,
    STEP_DOWNLOAD,
    STEP_KILL,
    STEP_LOCAL,
    STEP_POST_SETUP,
    STEP_POST_UPLOAD,
    STEP_PRE_RUN,
    STEP_PRE_SETUP,
    STEP_RUN,
    STEP_SETUP,
    STEP_UPLOAD,
)
from tests.e2e.helpers.logs import log_msg
from tests.e2e.helpers.runners import (
    finalize,
    ls,
    ls_files,
    neuro_ls,
    neuro_rm_dir,
    parse_job_id,
    parse_job_url,
    parse_jobs_ids,
    repeat_until_success,
    run,
    wait_job_change_status_to,
)
from tests.e2e.helpers.utils import cleanup_local_dirs, measure_time


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_help_works() -> None:
    out = run("make help")
    assert "setup" in out, f"not found in output: `{out}`"


@pytest.mark.run(order=STEP_LOCAL)
def test_make_lint() -> None:
    # just check exit code
    cmd = "make lint"
    run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_LOCAL + 1)
def test_make_format() -> None:
    # just check exit code
    cmd = "make format"
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
        _run_make_setup_test()
    except Exception:
        pytest.exit(f"Test on `make setup` failed, aborting the whole test suite.")
        raise


@finalize(f"neuro kill {MK_SETUP_JOB}")
def _run_make_setup_test() -> None:
    project_files_messages = []
    for file in MK_PROJECT_FILES:
        project_files_messages.append(_pattern_copy_file_started(file))
        project_files_messages.append(_pattern_copy_file_finished(file))
    # TODO: test also pre-installed APT packages
    apt_deps_messages = [
        f"Selecting previously unselected package {entry}"
        for entry in PACKAGES_APT_CUSTOM
    ]
    pip_deps_messages = [
        r"(Successfully installed|Collecting|Requirement already)[^\n]*" + pip
        for pip in PACKAGES_PIP_CUSTOM
    ]

    expected_patterns = [
        # run
        _get_pattern_status_running(),
        # apt-get install
        *apt_deps_messages,
        # pip install
        # (pip works either with stupid progress bars, or completely silently)
        *pip_deps_messages,
        # neuro save
        rf"Saving .*{JOB_ID_PATTERN}",
        r"Creating image",
        r"Image created",
        r"Pushing image",
        r"image://.*",
        # neuro kill
        r"neuro[\w\- ]* kill ",
        JOB_ID_PATTERN,
    ]

    make_cmd = "make setup"
    with measure_time(make_cmd, TIMEOUT_MAKE_SETUP):
        run(
            make_cmd,
            expect_patterns=expected_patterns,
            attempts=3,
            attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
        )


@pytest.mark.run(order=STEP_POST_SETUP)
@finalize(f"neuro kill {MK_SETUP_JOB}")
def test_make_kill_setup() -> None:
    # just check exit code
    run("make kill-setup", detect_new_jobs=False)


@pytest.mark.run(order=STEP_PRE_RUN)
def test_import_code_in_notebooks(
    env_var_preset_cpu_small: None, env_var_no_http_auth: None
) -> None:
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        assert "demo.ipynb" in neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
        assert "train.py" in neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")

        cmd = "make jupyter"
        nb_path = f"{MK_PROJECT_PATH_ENV}/{MK_NOTEBOOKS_DIR}/demo.ipynb"
        with measure_time(cmd, TIMEOUT_NEURO_RUN_CPU):
            run(
                cmd,
                expect_patterns=[_get_pattern_status_running()],
                error_patterns=[
                    fr"pattern '{nb_path}' matched no files",
                    "CellExecutionError",
                    "ModuleNotFoundError",
                ],
                attempts=3,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                assert_exit_code=False,
            )

        run(
            f'neuro exec --no-key-check --no-tty {MK_JUPYTER_JOB} "stat {nb_path}"',
            attempts=2,
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
            attempts=2,
            expect_patterns=[fr"Writing \d+ bytes to {out_file}", expected_string],
            error_patterns=["Error: ", "CRITICAL"],
            detect_new_jobs=False,
        )

        cmd = "make kill-jupyter"
        with measure_time(cmd):
            run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_UPLOAD)
def test_make_upload_code() -> None:
    assert ls_files(MK_CODE_DIR) == PROJECT_CODE_DIR_CONTENT
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}", timeout_s=TIMEOUT_NEURO_RMDIR_CODE
    )

    make_cmd = "make upload-code"
    with measure_time(make_cmd, TIMEOUT_MAKE_UPLOAD_CODE):
        run(make_cmd)
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")
    assert actual == PROJECT_CODE_DIR_CONTENT


@pytest.mark.run(order=STEP_UPLOAD)
def test_make_upload_data() -> None:
    assert len(ls_files(MK_DATA_DIR)) == N_FILES
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}", timeout_s=TIMEOUT_NEURO_RMDIR_DATA
    )

    make_cmd = "make upload-data"
    with measure_time(make_cmd, TIMEOUT_MAKE_UPLOAD_DATA):
        run(make_cmd)

    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)


@pytest.mark.run(order=STEP_UPLOAD)
def test_make_upload_config(
    decrypt_gcp_key: None, decrypt_aws_key: None, decrypt_wandb_key: None
) -> None:
    assert ls_files(MK_CONFIG_DIR) == PROJECT_CONFIG_DIR_CONTENT
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_CONFIG_DIR}",
        timeout_s=TIMEOUT_NEURO_RMDIR_CONFIG,
    )

    make_cmd = "make upload-config"
    with measure_time(make_cmd, TIMEOUT_MAKE_UPLOAD_CONFIG):
        run(make_cmd)

    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CONFIG_DIR}")
    assert actual == PROJECT_CONFIG_DIR_CONTENT


@pytest.mark.run(order=STEP_UPLOAD)
def test_make_upload_notebooks() -> None:
    assert ls_files(MK_NOTEBOOKS_DIR) == PROJECT_NOTEBOOKS_DIR_CONTENT
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}",
        timeout_s=TIMEOUT_NEURO_RMDIR_NOTEBOOKS,
    )

    make_cmd = "make upload-notebooks"
    with measure_time(make_cmd, TIMEOUT_MAKE_UPLOAD_NOTEBOOKS):
        run(make_cmd)

    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT


@pytest.mark.run(order=STEP_UPLOAD)
def test_make_upload_results() -> None:
    assert ls(MK_RESULTS_DIR) == PROJECT_RESULTS_DIR_CONTENT
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_DIR}",
        timeout_s=TIMEOUT_NEURO_RMDIR_NOTEBOOKS,
    )

    make_cmd = "make upload-results"
    with measure_time(make_cmd, TIMEOUT_MAKE_UPLOAD_RESULTS):
        run(make_cmd)

    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_DIR}")
    assert actual_remote == PROJECT_RESULTS_DIR_CONTENT


@pytest.mark.run(order=STEP_POST_UPLOAD)
def test_make_upload_all() -> None:
    # just check exit code
    cmd = "make upload-all"
    run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_DOWNLOAD)
def test_make_download_data() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")
    assert len(actual_remote) == N_FILES

    # Download:
    make_cmd = "make download-data"
    cleanup_local_dirs(MK_DATA_DIR)
    with measure_time(make_cmd, TIMEOUT_MAKE_DOWNLOAD_DATA):
        run(make_cmd)

    assert len(ls_files(MK_DATA_DIR)) == N_FILES


@pytest.mark.run(order=STEP_DOWNLOAD)
def test_make_download_noteboooks() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT

    make_cmd = "make download-notebooks"
    cleanup_local_dirs(MK_NOTEBOOKS_DIR)
    with measure_time(make_cmd, TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS):
        run(make_cmd)

    assert ls_files(MK_NOTEBOOKS_DIR) == PROJECT_NOTEBOOKS_DIR_CONTENT


@pytest.mark.run(order=STEP_DOWNLOAD)
def test_make_download_config() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CONFIG_DIR}")
    assert actual_remote == PROJECT_CONFIG_DIR_CONTENT

    make_cmd = "make download-config"
    cleanup_local_dirs(MK_CONFIG_DIR)
    with measure_time(make_cmd, TIMEOUT_MAKE_DOWNLOAD_CONFIG):
        run(make_cmd)

    assert ls_files(MK_CONFIG_DIR) == PROJECT_CONFIG_DIR_CONTENT


@pytest.mark.run(order=STEP_DOWNLOAD)
def test_make_download_results() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_DIR}")
    assert actual_remote == PROJECT_RESULTS_DIR_CONTENT

    # Download:
    make_cmd = "make download-results"
    cleanup_local_dirs(MK_RESULTS_DIR)
    with measure_time(make_cmd, TIMEOUT_MAKE_DOWNLOAD_RESULTS):
        run(make_cmd)

    assert ls(MK_RESULTS_DIR) == PROJECT_RESULTS_DIR_CONTENT


@pytest.mark.run(order=STEP_DOWNLOAD)
def test_make_download_all() -> None:
    cmd = "make download-all"
    with measure_time(cmd):
        run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_defaults(env_var_preset_cpu_small: None) -> None:
    with finalize(f"neuro kill {mk_train_job()}"):
        out = run(
            "make train",
            expect_patterns=[_get_pattern_status_succeeded_or_running()],
            attempts=3,
            attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
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
            "make train",
            expect_patterns=[_get_pattern_status_succeeded_or_running()],
            attempts=3,
            attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
        )
        job_id = parse_job_id(out)
        wait_job_change_status_to(job_id, JOB_STATUS_SUCCEEDED)


@pytest.mark.run(order=STEP_RUN)
def test_make_train_multiple_experiments(
    env_var_preset_cpu_small: None, neuro_project_id: str
) -> None:
    experiments = [MK_RUN_DEFAULT, "new-idea"]
    jobs = [mk_train_job(exp) for exp in experiments]
    with finalize(*[f"neuro kill {job}" for job in jobs]):
        for exp in experiments:
            cmd = f'make train TRAIN_CMD="sleep 1h"'
            if exp != MK_RUN_DEFAULT:
                cmd += f" RUN={exp}"
            with measure_time(cmd, TIMEOUT_NEURO_RUN_CPU):
                out = run(
                    cmd,
                    expect_patterns=[_get_pattern_status_running()],
                    attempts=3,
                    attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                    assert_exit_code=False,
                )
        ps_cmd = f'neuro -q ps --description="{neuro_project_id}:train"'

        out = run(ps_cmd, detect_new_jobs=False)
        assert len(out.split()) == len(jobs)

        run("make kill-train-all", detect_new_jobs=False)

        out = run(ps_cmd, detect_new_jobs=False)
        assert not out.strip()


@pytest.mark.run(order=STEP_RUN)
def test_make_train_invalid_name() -> None:
    run(
        "make train RUN=InVaLiD-NaMe",
        expect_patterns=["Invalid job name"],
        assert_exit_code=False,
        check_default_errors=False,
    )


@pytest.mark.run(order=STEP_RUN)
def test_make_train_tqdm(env_var_preset_cpu_small: str, monkeypatch: Any) -> None:
    with finalize(f"neuro kill {mk_train_job()}"):
        cmd = (
            'python -c "import time, tqdm; '
            '[time.sleep(0.1) for _ in tqdm.tqdm(range(10000))]"'
        )
        assert "'" not in cmd, f"cmd contains single quotes: `{cmd}`"
        log_msg(f"Setting env var: TRAIN_CMD=`{cmd}`")
        monkeypatch.setenv("TRAIN_CMD", cmd)

        tqdm_pattern = r"\d+%.*\d+/10000"
        cmd = "make train"
        with measure_time(cmd):
            run(
                cmd,
                detect_new_jobs=True,
                expect_patterns=[
                    _get_pattern_status_running(),
                    r"Streaming logs of the job",
                    tqdm_pattern,
                ],
                error_patterns=["[Ee]rror"],
                assert_exit_code=False,
            )

        run(
            "make stream-train",
            detect_new_jobs=False,
            expect_patterns=[tqdm_pattern],
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

    n = 2
    with finalize("make kill-hypertrain-all"):
        out = run(
            f"make hypertrain N_HYPERPARAM_JOBS={n}",
            expect_patterns=(
                [_get_pattern_status_running()] * n
                + [f"Started {n} hyper-parameter search jobs"]
            ),
        )
        jobs = parse_jobs_ids(out, expect_num=n)

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
def test_make_run_jupyter_notebook(
    env_neuro_run_timeout: int, env_var_no_http_auth: None
) -> None:
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        _test_run_something_useful("jupyter", "/tree", env_neuro_run_timeout)


@pytest.mark.run(order=STEP_RUN)
def test_make_jupyter_lab(
    env_var_no_http_auth: None, env_neuro_run_timeout: int
) -> None:
    with finalize(f"neuro kill {MK_JUPYTER_JOB}"):
        _test_run_something_useful("jupyter", "/lab", env_neuro_run_timeout)


@pytest.mark.run(order=STEP_RUN)
def test_make_tensorboard(env_var_no_http_auth: None) -> None:
    with finalize(f"neuro kill {MK_TENSORBOARD_JOB}"):
        _test_run_something_useful("tensorboard", "/", TIMEOUT_NEURO_RUN_CPU)


@pytest.mark.run(order=STEP_RUN)
def test_make_filebrowser(env_var_no_http_auth: None) -> None:
    with finalize(f"neuro kill {MK_FILEBROWSER_JOB}"):
        _test_run_something_useful(
            "filebrowser", "/files/requirements.txt", TIMEOUT_NEURO_RUN_CPU
        )


def _test_run_something_useful(target: str, path: str, timeout_run: int) -> None:
    # Can't test web UI with HTTP auth
    make_cmd = f"make {target}"
    with measure_time(make_cmd, timeout_run):
        out = run(
            make_cmd,
            expect_patterns=[_get_pattern_status_running()],
            attempts=3,
            attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
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
        run(make_cmd, timeout_s=TIMEOUT_NEURO_KILL)
    wait_job_change_status_to(job_id, JOB_STATUS_SUCCEEDED)


@pytest.mark.run(order=STEP_RUN)
def test_gpu_available(environment: str) -> None:
    if environment in ["dev"]:
        pytest.skip(f"Skipped as GPU is not available on {environment}")
    with finalize(f"neuro kill {MK_DEVELOP_JOB}"):
        cmd = "make develop PRESET=gpu-small"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=3,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                timeout_s=TIMEOUT_NEURO_RUN_GPU,
            )

        py_commands = [
            "import tensorflow as tf; assert tf.test.is_gpu_available()",
            "import torch; print(torch.randn(2,2).cuda())",
            "import torch; assert torch.cuda.is_available()",
        ]
        for py in py_commands:
            cmd = (
                f"neuro exec --no-key-check --no-tty {MK_DEVELOP_JOB} "
                f"\"python -c '{py}'\""
            )
            with measure_time(cmd):
                run(cmd, attempts=2, timeout_s=TIMEOUT_NEURO_EXEC)


@pytest.mark.run(order=STEP_RUN)
def test_make_develop_all(env_neuro_run_timeout: int) -> None:
    with finalize(f"neuro kill {MK_DEVELOP_JOB}"):
        cmd = "make develop"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=[r"Status:[^\n]+running"],
                attempts=3,
                attempt_substrings=DEFAULT_ERROR_SUBSTRINGS_JOB_RUN,
                timeout_s=env_neuro_run_timeout,
            )

        cmd = "make connect-develop"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=[_get_pattern_connected_ssh()],
                timeout_s=TIMEOUT_NEURO_EXEC,
                assert_exit_code=False,
            )
        # TODO: improve this test by sending command `echo 123`
        #  and then reading it via `make logs-develop` (needs improvements of runners)

        cmd = "make logs-develop"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=["Starting SSH server"],
                timeout_s=TIMEOUT_NEURO_LOGS,
                assert_exit_code=False,
            )

        cmd = "make stream-develop"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=["Starting SSH server"],
                timeout_s=TIMEOUT_NEURO_LOGS,
                assert_exit_code=False,
            )

        cmd = "make port-forward-develop"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=[r"Press \^C to stop forwarding"],
                timeout_s=TIMEOUT_NEURO_PORT_FORWARD,
                assert_exit_code=False,
            )

        cmd = "make kill-develop"
        with measure_time(cmd):
            run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_KILL)
def test_make_connect_train_kill_train(env_var_preset_cpu_small: None) -> None:
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

        cmd = "make kill-train"
        with measure_time(cmd):
            run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_KILL)
def test_make_kill_all() -> None:
    # just check exit code
    cmd = f"make kill-all"
    with measure_time(cmd):
        run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_CLEANUP)
def test_make_clean_code() -> None:
    assert neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")

    # just check exit code
    make_cmd = "make clean-code"
    with measure_time(make_cmd):
        run(make_cmd)

    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
def test_make_clean_config(
    decrypt_gcp_key: None, decrypt_aws_key: None, decrypt_wandb_key: None
) -> None:
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CONFIG_DIR}")
    assert actual == PROJECT_CONFIG_DIR_CONTENT

    make_cmd = "make clean-config"
    with measure_time(make_cmd):
        run(
            make_cmd,
            timeout_s=TIMEOUT_MAKE_UPLOAD_CONFIG,
            # TODO: add clean-specific error patterns
        )
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CONFIG_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
def test_make_clean_data() -> None:
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)

    make_cmd = "make clean-data"
    with measure_time(make_cmd):
        run(
            make_cmd,
            timeout_s=TIMEOUT_MAKE_CLEAN_DATA,
            # TODO: add clean-specific error patterns
        )
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
def test_make_clean_notebooks() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT

    make_cmd = "make clean-notebooks"
    with measure_time(make_cmd):
        run(
            make_cmd,
            timeout_s=TIMEOUT_MAKE_CLEAN_NOTEBOOKS,
            # TODO: add clean-specific error patterns
        )
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
def test_make_clean_results() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_DIR}")
    assert actual_remote >= PROJECT_RESULTS_DIR_CONTENT

    make_cmd = "make clean-results"
    with measure_time(make_cmd):
        run(make_cmd, timeout_s=TIMEOUT_MAKE_CLEAN_RESULTS)
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_RESULTS_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
def test_make_clean_all() -> None:
    # just check exit code
    cmd = "make clean-all"
    with measure_time(cmd):
        run(cmd, detect_new_jobs=False)


@pytest.mark.run(order=STEP_LOCAL)
def test_make_setup_local() -> None:
    # just check exit code
    cmd = "make setup-local"
    run(
        cmd,
        expect_patterns=[
            _get_pattern_pip_installing(pip) for pip in PACKAGES_PIP_CUSTOM
        ],
        detect_new_jobs=False,
    )
