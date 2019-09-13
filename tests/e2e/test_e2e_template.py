import os
from pathlib import Path

import pytest

from .configuration import *
from .conftest import *


log = get_logger()


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
        "setup.py",
        "setup.cfg",
        ".gitignore",
    }


def test_make_help_works() -> None:
    out = run_command("make help", debug=True)
    assert "setup" in out, f"not found in output: `{out}`"


@pytest.mark.run(order=1)
def test_make_setup() -> None:
    make_cmd = "make setup"

    # TODO: test also pre-installed APT packages
    apt_deps_messages = [
        f"Selecting previously unselected package {entry}"
        for entry in PACKAGES_APT_USER
    ]
    # TODO: test also pre-installed PIP packages
    pip_deps_entries = sorted(
        [entry.replace("==", "-").replace("_", "-") for entry in PACKAGES_PIP_USER]
    )
    pip_deps_message = r"Successfully installed [^\n]* " + r"[^\n]*".join(
        pip_deps_entries
    )

    expected_patterns = [
        # run
        r"Status:[^\n]+running",
        # copy apt.txt
        f"Copy 'file://.*{PROJECT_APT_FILE_NAME}",
        rf"'{PROJECT_APT_FILE_NAME}' \d+B",
        # copy pep.txt
        f"Copy 'file://.*{PROJECT_PIP_FILE_NAME}",
        rf"'{PROJECT_PIP_FILE_NAME}' \d+B",
        # apt-get install
        *apt_deps_messages,
        r"APT requirements installation completed",
        # pip install
        # (pip works either with stupid progress bars, or completely silently)
        pip_deps_message,
        r"PIP requirements installation completed",
        # neuro save
        r"Saving .+ \->",
        r"Creating image",
        r"Image created",
        r"Pushing image .+ => .+",
        r"image://.*",
        # neuro kill
        "neuro kill",
        r"job\-[^\n]+",
        # success
        r"Project setup completed",
    ]

    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_SETUP,
            expect_patterns=expected_patterns,
            # TODO: add specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    # run_command("neuro ls stor)


@pytest.mark.run(order=2)
def test_make_upload_code() -> None:
    make_cmd = "make upload-code"

    neuro_rm_dir(
        MK_CODE_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS, ignore_errors=True
    )

    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_UPLOAD_CODE,
            expect_patterns=[rf"'file://.*/{MK_CODE_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(MK_CODE_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS)
    assert actual == {"main.py"}


@pytest.mark.run(order=3)
def test_make_clean_code() -> None:
    make_cmd = "make clean-code"
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_UPLOAD_CODE,
            # no expected output
            # TODO: add clean-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    with pytest.raises(RuntimeError, match="404: Not Found"):
        neuro_ls(MK_CODE_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS)


@pytest.mark.run(order=4)
def test_make_upload_data() -> None:
    make_cmd = "make upload-data"

    neuro_rm_dir(
        MK_DATA_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS, ignore_errors=True
    )

    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_UPLOAD_DATA,
            expect_patterns=[rf"'file://.*/{MK_DATA_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(MK_DATA_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS)
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)


@pytest.mark.run(order=5)
def test_make_clean_data() -> None:
    make_cmd = "make clean-data"
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_CLEAN_DATA,
            # no expected output
            # TODO: add clean-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    with pytest.raises(RuntimeError, match="404: Not Found"):
        neuro_ls(MK_DATA_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS)


@pytest.mark.run(order=6)
def test_make_upload_download_notebooks() -> None:
    files_set = {"00_notebook_tutorial.ipynb", "__init__.py"}

    make_cmd = "make upload-notebooks"
    neuro_rm_dir(
        MK_NOTEBOOKS_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS, ignore_errors=True
    )
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_UPLOAD_NOTEBOOKS,
            expect_patterns=[rf"'file://.*/{MK_NOTEBOOKS_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual_remote = neuro_ls(
        MK_NOTEBOOKS_PATH_STORAGE, timeout=TIMEOUT_NEURO_STORAGE_LS
    )
    assert actual_remote == files_set

    make_cmd = "make download-notebooks"
    cleanup_local_dirs(MK_NOTEBOOKS_PATH)
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_DOWNLOAD_NOTEBOOKS,
            expect_patterns=[rf"'storage://.*/{MK_NOTEBOOKS_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual_local = {f.name for f in Path(MK_NOTEBOOKS_PATH).iterdir()}
    assert actual_local == files_set
