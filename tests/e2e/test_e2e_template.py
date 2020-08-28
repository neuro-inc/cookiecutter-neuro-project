import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from flaky import flaky

from tests.e2e.configuration import (
    EXISTING_PROJECT_SLUG,
    JOB_ID_PATTERN,
    JOB_STATUS_SUCCEEDED,
    MK_CODE_DIR,
    MK_DEVELOP_JOB,
    MK_JUPYTER_JOB,
    MK_NOTEBOOKS_DIR,
    MK_PROJECT,
    MK_PROJECT_PATH_ENV,
    MK_PROJECT_PATH_STORAGE,
    MK_SETUP_JOB,
    MK_TENSORBOARD_JOB,
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
    run(cmd,)


@pytest.mark.run(order=STEP_LOCAL)
def test_make_lint_local() -> None:
    cmd = "make lint-local"
    run(cmd,)


@pytest.mark.run(order=STEP_LOCAL + 1)
def test_make_format_local() -> None:
    cmd = "make format-local"
    run(cmd,)


@pytest.mark.run(order=STEP_PRE_SETUP)
def test_make_setup_required() -> None:
    run(
        "make jupyter",
        expect_patterns=["Please run 'make setup' first"],
        assert_exit_code=False,
        check_default_errors=False,
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
            run("make kill-setup",)
    except Exception:
        pytest.exit(f"Test on `make setup` failed, aborting the whole test suite.")
        raise


@pytest.mark.run(order=STEP_PRE_RUN)
@flaky(max_runs=3)
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

        run(f'neuro exec --no-key-check --no-tty {MK_JUPYTER_JOB} "stat {nb_path}"',)

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
        )

        cmd = "make kill-jupyter"
        with measure_time(cmd):
            run(cmd,)


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
def test_make_train_defaults(monkeypatch: Any, env_var_preset_cpu_small: None) -> None:
    monkeypatch.setenv("RUN_EXTRA", "--detach")
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
    monkeypatch.setenv("RUN_EXTRA", "--detach")

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
def test_make_run_jupyter_notebook(env_var_no_http_auth: None) -> None:
    _test_run_something_useful("jupyter", MK_JUPYTER_JOB, "/tree")


@pytest.mark.run(order=STEP_RUN)
def test_make_jupyter_lab(env_var_no_http_auth: None,) -> None:
    _test_run_something_useful("jupyter", MK_JUPYTER_JOB, "/lab")


@pytest.mark.run(order=STEP_RUN)
def test_make_tensorboard(env_var_no_http_auth: None) -> None:
    _test_run_something_useful("tensorboard", MK_TENSORBOARD_JOB, "/")


def _test_run_something_useful(target: str, job_name: str, path: str) -> None:
    # Can't test web UI with HTTP auth
    with finalize(f"neuro kill {job_name}"):
        make_cmd = f"make {target}"
        with measure_time(make_cmd):
            out = run(
                make_cmd,
                expect_patterns=[_get_pattern_status_running()],
                assert_exit_code=False,
            )
        job_id = parse_job_id(out)
        url = parse_job_url(run(f"neuro status {job_name}"))

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
            run(cmd, expect_patterns=[_get_pattern_status_running()])

        cmd = "make kill-develop"
        with measure_time(cmd):
            run(cmd)


@pytest.mark.run(order=STEP_RUN)
@pytest.mark.timeout(5 * 60)
@flaky(max_runs=3)
@pytest.mark.skipif(
    sys.platform == "win32", reason="FIXME: Incorrect secret path on Windows"
)
def test_gsutil_auth_works_from_python_api(
    gcp_secret_mount: None, env_var_preset_cpu_small: None, monkeypatch: Any
) -> None:
    monkeypatch.setenv("SECRETS", gcp_secret_mount)

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
        run(make_cmd)

    make_cmd = f'make train TRAIN_CMD="python {script_path}"'
    with finalize(f"neuro kill {mk_train_job()}"):
        with measure_time(make_cmd):
            out = run(make_cmd)

        job_id = parse_job_id(out)

        cmd = f"neuro logs {job_id}"
        with measure_time(cmd):
            run(
                cmd,
                expect_patterns=["Hello world!"],
                error_patterns=["Errno", "No such file or directory"],
            )


@pytest.mark.run(order=STEP_KILL)
def test_make_kill_all() -> None:
    cmd = f"make kill-all"
    with measure_time(cmd):
        run(cmd)
