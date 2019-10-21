from pathlib import Path
from time import sleep

import pytest

from tests.e2e.configuration import (
    MK_CODE_PATH,
    MK_CODE_PATH_STORAGE,
    MK_DATA_PATH,
    MK_DATA_PATH_STORAGE,
    MK_FILEBROWSER_NAME,
    MK_JUPYTER_NAME,
    MK_NOTEBOOKS_PATH,
    MK_NOTEBOOKS_PATH_ENV,
    MK_NOTEBOOKS_PATH_STORAGE,
    MK_SETUP_NAME,
    MK_TENSORBOARD_NAME,
    N_FILES,
    PACKAGES_APT_CUSTOM,
    PACKAGES_PIP_CUSTOM,
    PROJECT_APT_FILE_NAME,
    PROJECT_CODE_DIR_CONTENT,
    PROJECT_HIDDEN_FILES,
    PROJECT_NOTEBOOKS_DIR_CONTENT,
    PROJECT_PIP_FILE_NAME,
    PROJECT_PYTHON_FILES,
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
)
from .conftest import (
    DEFAULT_ERROR_PATTERNS,
    cleanup_local_dirs,
    get_logger,
    measure_time,
    neuro_ls,
    neuro_rm_dir,
    parse_job_id,
    parse_job_url,
    repeat_until_success,
    run,
    timeout,
    try_except_finally,
    wait_job_change_status_to,
)


log = get_logger()


@try_except_finally()
def test_project_structure() -> None:
    dirs = {f.name for f in Path().iterdir() if f.is_dir()}
    assert dirs == {MK_DATA_PATH, MK_CODE_PATH, MK_NOTEBOOKS_PATH}
    files = {f.name for f in Path().iterdir() if f.is_file()}
    assert files == {
        "Makefile",
        "README.md",
        "LICENSE",
        PROJECT_APT_FILE_NAME,
        PROJECT_PIP_FILE_NAME,
        "setup.cfg",
        ".gitignore",
    }


@pytest.mark.run(order=0)
@try_except_finally()
def test_make_help_works() -> None:
    out = run("make help", verbose=True)
    assert "setup" in out, f"not found in output: `{out}`"


@pytest.mark.run(order=1)
def test_make_setup(tmp_path: Path) -> None:
    _run_make_setup_test(tmp_path)


@try_except_finally(f"neuro kill {MK_SETUP_NAME}")
def _run_make_setup_test(tmp_path: Path) -> None:
    project_files_messages = [f"Copy 'file://.*{file}" for file in PROJECT_PYTHON_FILES]
    # TODO: test also pre-installed APT packages
    apt_deps_messages = [
        f"Selecting previously unselected package {entry}"
        for entry in PACKAGES_APT_CUSTOM
    ]
    # TODO: test also pre-installed PIP packages
    pip_deps_entries = sorted(
        [entry.replace("==", "-").replace("_", "-") for entry in PACKAGES_PIP_CUSTOM]
    )
    pip_deps_message = r"Successfully installed [^\n]* " + r"[^\n]*".join(
        pip_deps_entries
    )

    expected_patterns = [
        # run
        r"Status:[^\n]+running",
        # copy project files
        *project_files_messages,
        # copy apt.txt
        f"Copy 'file://.*{PROJECT_APT_FILE_NAME}",
        rf"'{PROJECT_APT_FILE_NAME}' \d+B",
        # copy pep.txt
        f"Copy 'file://.*{PROJECT_PIP_FILE_NAME}",
        rf"'{PROJECT_PIP_FILE_NAME}' \d+B",
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
        "neuro kill",
        r"job\-[^\n]+",
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

    # Test imports from a notebook:
    out = run(
        "make jupyter DISABLE_HTTP_AUTH=True TRAINING_MACHINE_TYPE=cpu-small",
        verbose=True,
        expect_patterns=[r"Status:[^\n]+running"],
        timeout_s=TIMEOUT_NEURO_RUN_CPU,
    )
    job_id = parse_job_id(out)

    expected_string = "Hello World!"
    tmp_path.mkdir(exist_ok=True)
    out_file = (tmp_path / "out").absolute()
    cmd = (
        "jupyter nbconvert --execute --no-prompt --no-input --to=asciidoc "
        f"--output={out_file} {MK_NOTEBOOKS_PATH_ENV}/Untitled.ipynb && "
        f"cat {out_file}.asciidoc && "
        f'grep "{expected_string}" {out_file}.asciidoc'
    )
    run(
        f"neuro exec --no-key-check --no-tty {job_id} 'bash -c \"{cmd}\"'",
        verbose=True,
        expect_patterns=[r"Writing \d+ bytes to .*out.asciidoc"],
        error_patterns=["(E|e)rror:"],
    )


@pytest.mark.run(order=2)
@try_except_finally()
def test_make_upload_code() -> None:
    neuro_rm_dir(
        MK_CODE_PATH_STORAGE, timeout_s=TIMEOUT_NEURO_RMDIR_CODE, ignore_errors=True
    )

    # Upload:
    make_cmd = "make upload-code"
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_CODE,
            expect_patterns=[rf"'file://.*/{MK_CODE_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(MK_CODE_PATH_STORAGE)
    assert actual == PROJECT_CODE_DIR_CONTENT


@pytest.mark.run(order=2)
@try_except_finally()
def test_make_upload_data() -> None:
    neuro_rm_dir(
        MK_DATA_PATH_STORAGE, timeout_s=TIMEOUT_NEURO_RMDIR_DATA, ignore_errors=True
    )

    make_cmd = "make upload-data"
    # Upload:
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_DATA,
            expect_patterns=[rf"'file://.*/{MK_DATA_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    # TODO: HACK: let storage sync
    sleep(5)
    actual = neuro_ls(MK_DATA_PATH_STORAGE)
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)


@pytest.mark.run(order=2)
@try_except_finally()
def test_make_upload_download_notebooks() -> None:
    # Upload:
    make_cmd = "make upload-notebooks"
    neuro_rm_dir(
        MK_NOTEBOOKS_PATH_STORAGE,
        timeout_s=TIMEOUT_NEURO_RMDIR_NOTEBOOKS,
        ignore_errors=True,
    )
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_UPLOAD_NOTEBOOKS,
            expect_patterns=[rf"'file://.*/{MK_NOTEBOOKS_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual_remote = neuro_ls(MK_NOTEBOOKS_PATH_STORAGE)
    assert actual_remote == PROJECT_NOTEBOOKS_DIR_CONTENT

    # Download:
    make_cmd = "make download-notebooks"
    cleanup_local_dirs(MK_NOTEBOOKS_PATH)
    with measure_time(make_cmd):
        run(
            make_cmd,
            verbose=True,
            timeout_s=TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS,
            expect_patterns=[rf"'storage://.*/{MK_NOTEBOOKS_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            error_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual_local = {
        path.name
        for path in Path(MK_NOTEBOOKS_PATH).iterdir()
        if path.name not in PROJECT_HIDDEN_FILES
    }
    assert actual_local == PROJECT_NOTEBOOKS_DIR_CONTENT


# TODO: training, kill-training, connect-training


@pytest.mark.run(order=3)
@try_except_finally(f"neuro kill {MK_JUPYTER_NAME}")
def test_make_run_jupyter() -> None:
    _test_make_run_something_useful("jupyter", "/tree", TIMEOUT_NEURO_RUN_GPU)


@pytest.mark.run(order=3)
@try_except_finally(f"neuro kill {MK_TENSORBOARD_NAME}")
def test_make_run_tensorboard() -> None:
    _test_make_run_something_useful("tensorboard", "/", TIMEOUT_NEURO_RUN_CPU)


@pytest.mark.run(order=3)
@try_except_finally(f"neuro kill {MK_FILEBROWSER_NAME}")
def test_make_run_filebrowser() -> None:
    _test_make_run_something_useful("filebrowser", "/login", TIMEOUT_NEURO_RUN_CPU)


def _test_make_run_something_useful(target: str, path: str, timeout_run: int) -> None:
    # Can't test web UI with HTTP auth
    make_cmd = f"make {target} DISABLE_HTTP_AUTH=True"
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


@pytest.mark.run(order=4)
@try_except_finally()
def test_make_clean_code() -> None:
    actual = neuro_ls(MK_CODE_PATH_STORAGE)
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
    with pytest.raises(RuntimeError, match="404: Not Found"):
        neuro_ls(MK_CODE_PATH_STORAGE)


@pytest.mark.run(order=4)
@try_except_finally()
def test_make_clean_data() -> None:
    actual = neuro_ls(MK_DATA_PATH_STORAGE)
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
    with pytest.raises(RuntimeError, match="404: Not Found"):
        neuro_ls(MK_DATA_PATH_STORAGE)


@pytest.mark.run(order=4)
@try_except_finally()
def test_make_clean_notebooks() -> None:
    actual_remote = neuro_ls(MK_NOTEBOOKS_PATH_STORAGE)
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
    with pytest.raises(RuntimeError, match="404: Not Found"):
        neuro_ls(MK_NOTEBOOKS_PATH_STORAGE)


# TODO: other tests
