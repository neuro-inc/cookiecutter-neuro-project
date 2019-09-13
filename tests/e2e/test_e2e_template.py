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

    make_cmd = "make setup"
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_SETUP,
            expect_patterns=expected_patterns,
            # TODO: add specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )


@pytest.mark.run(order=2)
def test_make_upload_clean_code() -> None:
    neuro_rm_dir(MK_CODE_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS, ignore_errors=True)

    # Upload:
    make_cmd = "make upload-code"
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_UPLOAD_CODE,
            expect_patterns=[rf"'file://.*/{MK_CODE_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(MK_CODE_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS)
    assert actual == {"main.py"}

    # Clean:
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
        neuro_ls(MK_CODE_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS)


@pytest.mark.run(order=3)
def test_make_upload_clean_data() -> None:
    neuro_rm_dir(MK_DATA_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS, ignore_errors=True)

    make_cmd = "make upload-data"
    # Upload:
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_UPLOAD_DATA,
            expect_patterns=[rf"'file://.*/{MK_DATA_PATH}' DONE"],
            # TODO: add upload-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    actual = neuro_ls(MK_DATA_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS)
    assert len(actual) == N_FILES
    assert all(name.endswith(".tmp") for name in actual)

    # Clean:
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
        neuro_ls(MK_DATA_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS)


@pytest.mark.run(order=4)
def test_make_upload_download_clean_notebooks() -> None:
    files_set = {"00_notebook_tutorial.ipynb", "__init__.py"}

    # Upload:
    make_cmd = "make upload-notebooks"
    neuro_rm_dir(
        MK_NOTEBOOKS_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS, ignore_errors=True
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
    actual_remote = neuro_ls(MK_NOTEBOOKS_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS)
    assert actual_remote == files_set

    # Download:
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

    # Clean:
    make_cmd = "make clean-notebooks"
    with measure_time(make_cmd):
        run_command(
            make_cmd,
            debug=True,
            timeout=TIMEOUT_MAKE_CLEAN_NOTEBOOKS,
            # no expected output
            # TODO: add clean-specific error patterns
            stop_patterns=DEFAULT_ERROR_PATTERNS,
        )
    with pytest.raises(RuntimeError, match="404: Not Found"):
        neuro_ls(MK_NOTEBOOKS_PATH_STORAGE, timeout=TIMEOUT_NEURO_LS)


# TODO: test 'make upload', 'make clean'
