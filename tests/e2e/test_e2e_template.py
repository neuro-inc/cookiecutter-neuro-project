from pathlib import Path

import pytest

from tests.e2e.configuration import (
    DEFAULT_ERROR_PATTERNS,
    MK_CODE_DIR,
    MK_DATA_DIR,
    MK_FILEBROWSER_JOB,
    MK_JUPYTER_JOB,
    MK_NOTEBOOKS_DIR,
    MK_PROJECT_FILES,
    MK_PROJECT_PATH_ENV,
    MK_PROJECT_PATH_STORAGE,
    MK_PROJECT_SLUG,
    MK_SETUP_JOB,
    MK_TENSORBOARD_JOB,
    N_FILES,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PROJECT_CODE_DIR_CONTENT,
    PROJECT_HIDDEN_FILES,
    PROJECT_NOTEBOOKS_DIR_CONTENT,
    TIMEOUT_MAKE_CLEAN_DATA,
    TIMEOUT_MAKE_CLEAN_NOTEBOOKS,
    TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS,
    TIMEOUT_MAKE_SETUP,
    TIMEOUT_MAKE_UPLOAD_CODE,
    TIMEOUT_MAKE_UPLOAD_DATA,
    TIMEOUT_MAKE_UPLOAD_NOTEBOOKS,
    TIMEOUT_NEURO_KILL,
    TIMEOUT_NEURO_RMDIR_CODE,
    TIMEOUT_NEURO_RMDIR_DATA,
    TIMEOUT_NEURO_RMDIR_NOTEBOOKS,
    TIMEOUT_NEURO_RUN_CPU,
    TIMEOUT_NEURO_RUN_GPU,
    _pattern_copy_file_finished,
    _pattern_copy_file_started,
    _pattern_upload_dir,
)
from tests.e2e.helpers.runners import (
    neuro_ls,
    neuro_rm_dir,
    parse_job_id,
    parse_job_url,
    repeat_until_success,
    run,
    try_except_finally,
    wait_job_change_status_to,
)
from tests.e2e.helpers.utils import cleanup_local_dirs, measure_time, timeout


STEP_PRE_SETUP = 0
STEP_SETUP = 3
STEP_POST_SETUP = 7
STEP_UPLOAD = 10
STEP_DOWNLOAD = 20
STEP_RUN = 30
STEP_KILL = 90
STEP_CLEANUP = 100


@try_except_finally()
def test_project_structure() -> None:
    dirs = {f.name for f in Path().iterdir() if f.is_dir()}
    assert dirs == {MK_DATA_DIR, MK_CODE_DIR, MK_NOTEBOOKS_DIR}
    files = {f.name for f in Path().iterdir() if f.is_file()}
    assert files == {"Makefile", "README.md", ".gitignore", *MK_PROJECT_FILES}


@pytest.mark.run(order=STEP_PRE_SETUP)
@try_except_finally()
def test_make_help_works() -> None:
    out = run("make help", verbose=True)
    assert "setup" in out, f"not found in output: `{out}`"


@pytest.mark.run(order=STEP_SETUP)
def test_make_setup() -> None:
    try:
        _run_make_setup_test()
    except Exception:
        pytest.exit(f"Test on `make setup` failed, aborting the whole test suite.")
        raise


@try_except_finally(f"neuro kill {MK_SETUP_JOB}")
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
    # TODO: test also pre-installed PIP packages
    pip_deps = sorted(
        [entry.replace("==", "-").replace("_", "-") for entry in PACKAGES_PIP_CUSTOM]
    )
    pip_deps_message = r"Successfully installed [^\n]*" + r"[^\n]*".join(pip_deps)

    expected_patterns = [
        # run
        r"Status:[^\n]+running",
        # apt-get install
        *apt_deps_messages,
        # pip install
        # (pip works either with stupid progress bars, or completely silently)
        pip_deps_message,
        # neuro save
        r"Saving .+ \->",
        r"Creating image",
        r"Image created",
        r"Pushing image .+ => .+",
        r"image://.*",
        # neuro kill
        r"neuro[\w\- ]* kill [\w\- ]+\r\njob\-[^\n]+",
    ]

    make_cmd = "make setup"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_SETUP,
            expect_patterns=expected_patterns,
            # TODO: add specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )


@pytest.mark.run(order=STEP_RUN)
def test_import_code_in_notebooks() -> None:
    _run_import_code_in_notebooks_test()


@try_except_finally(f"neuro kill {MK_JUPYTER_JOB}")
def _run_import_code_in_notebooks_test() -> None:
    out = run(
        "make jupyter HTTP_AUTH=--no-http-auth TRAINING_MACHINE_TYPE=cpu-small",
        verbose=True,
        expect_patterns=[r"Status:[^\n]+running"],
        timeout_s=TIMEOUT_NEURO_RUN_CPU,
    )
    job_id = parse_job_id(out)

    expected_string = "----\r\nHello World!\r\n----"

    out_file = f"/tmp/out-nbconvert-{MK_PROJECT_SLUG}"
    jupyter_nbconvert_cmd = "jupyter nbconvert --execute --no-prompt --no-input"
    notebook_path = f"{MK_PROJECT_PATH_ENV}/{MK_NOTEBOOKS_DIR}/Untitled.ipynb"
    cmd = (
        f"{jupyter_nbconvert_cmd} --to=asciidoc --output={out_file} {notebook_path} &&"
        f"cat {out_file}.asciidoc"
    )
    run(
        f"neuro exec --no-key-check --no-tty {job_id} 'bash -c \"{cmd}\"'",
        verbose=True,
        expect_patterns=[fr"Writing \d+ bytes to {out_file}", expected_string],
        error_patterns=["Error: ", "CRITICAL"],
        detect_new_jobs=False,
    )


@pytest.mark.run(order=STEP_UPLOAD)
@try_except_finally()
def test_make_upload_code() -> None:
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}",
        timeout_s=TIMEOUT_NEURO_RMDIR_CODE,
        ignore_errors=True,
    )

    # Upload:
    make_cmd = "make upload-code"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_CODE,
            expect_patterns=[_pattern_upload_dir(MK_PROJECT_SLUG, MK_CODE_DIR)],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")
    assert actual == PROJECT_CODE_DIR_CONTENT


@pytest.mark.run(order=STEP_UPLOAD)
@try_except_finally()
def test_make_upload_data() -> None:
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}",
        timeout_s=TIMEOUT_NEURO_RMDIR_DATA,
        ignore_errors=True,
    )

    # Upload:
    make_cmd = "make upload-data"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_DATA,
            expect_patterns=[_pattern_upload_dir(MK_PROJECT_SLUG, MK_DATA_DIR)],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)


@pytest.mark.run(order=STEP_UPLOAD)
@try_except_finally()
def test_make_upload_notebooks() -> None:
    # Upload:
    make_cmd = "make upload-notebooks"
    neuro_rm_dir(
        f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}",
        timeout_s=TIMEOUT_NEURO_RMDIR_NOTEBOOKS,
        ignore_errors=True,
    )
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_NOTEBOOKS,
            expect_patterns=[_pattern_upload_dir(MK_PROJECT_SLUG, MK_NOTEBOOKS_DIR)],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT


@pytest.mark.run(order=STEP_DOWNLOAD)
@try_except_finally()
def test_make_download_noteboooks() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT

    # Download:
    make_cmd = "make download-notebooks"
    cleanup_local_dirs(MK_NOTEBOOKS_DIR)
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS,
            expect_patterns=[_pattern_upload_dir(MK_PROJECT_SLUG, MK_NOTEBOOKS_DIR)],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual_local = {
        path.name
        for path in Path(MK_NOTEBOOKS_DIR).iterdir()
        if path.name not in PROJECT_HIDDEN_FILES
    }
    assert actual_local == PROJECT_NOTEBOOKS_DIR_CONTENT


# TODO: training, kill-training, connect-training


@pytest.mark.run(order=STEP_KILL)
@try_except_finally(f"neuro kill {MK_JUPYTER_JOB}")
def test_make_run_jupyter() -> None:
    _test_make_run_something_useful("jupyter", "/tree", TIMEOUT_NEURO_RUN_GPU)


@pytest.mark.run(order=STEP_KILL)
@try_except_finally(f"neuro kill {MK_TENSORBOARD_JOB}")
def test_make_run_tensorboard() -> None:
    _test_make_run_something_useful("tensorboard", "/", TIMEOUT_NEURO_RUN_CPU)


@pytest.mark.run(order=STEP_KILL)
@try_except_finally(f"neuro kill {MK_FILEBROWSER_JOB}")
def test_make_run_filebrowser() -> None:
    _test_make_run_something_useful("filebrowser", "/login", TIMEOUT_NEURO_RUN_CPU)


def _test_make_run_something_useful(target: str, path: str, timeout_run: int) -> None:
    # Can't test web UI with HTTP auth
    make_cmd = f"make {target} HTTP_AUTH=--no-http-auth"
    with measure_time(make_cmd):
        out = run(
            make_cmd,
            verbose=True,
            timeout_s=timeout_run,
            expect_patterns=[r"Status:[^\n]+running"],
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )

    job_id = parse_job_id(out)
    url = parse_job_url(out)
    with timeout(2 * 60):
        repeat_until_success(
            f"curl --fail {url}{path}",
            job_id,
            expect_patterns=["<html.*>"],
            error_patterns=["curl: .+"],
            verbose=False,
        )

    make_cmd = f"make kill-{target}"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_NEURO_KILL,
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    wait_job_change_status_to(job_id, "succeeded")


@pytest.mark.run(order=STEP_CLEANUP)
@try_except_finally()
def test_make_clean_code() -> None:
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")
    assert actual == PROJECT_CODE_DIR_CONTENT

    make_cmd = "make clean-code"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_CODE,
            # TODO: add clean-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_CODE_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
@try_except_finally()
def test_make_clean_data() -> None:
    actual = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)

    make_cmd = "make clean-data"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_CLEAN_DATA,
            # TODO: add clean-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_DATA_DIR}")


@pytest.mark.run(order=STEP_CLEANUP)
@try_except_finally()
def test_make_clean_notebooks() -> None:
    actual_remote = neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT

    make_cmd = "make clean-notebooks"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_CLEAN_NOTEBOOKS,
            # TODO: add clean-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    assert not neuro_ls(f"{MK_PROJECT_PATH_STORAGE}/{MK_NOTEBOOKS_DIR}")


# TODO: other tests
