import os
from pathlib import Path

import pytest

from .conftest import (
    COOKIECUTTER_PROJECT_NAME,
    FILE_SIZE_B,
    FILE_SIZE_KB,
    N_FILES,
    PACKAGES_APT,
    TIMEOUT_NEURO_DOWNLOAD,
    TIMEOUT_NEURO_JOB_RUN,
    TIMEOUT_NEURO_STORAGE_LS,
    TIMEOUT_NEURO_STORAGE_RM,
    TIMEOUT_NEURO_UPLOAD,
    cleanup_local_dirs,
    generate_random_file,
    get_logger,
    measure_time,
    run_detach,
    run_detach_wait_substrings,
    run_once,
    COOKIECUTTER_APT_FILE_REL_PATH,
    COOKIECUTTER_PIP_FILE_REL_PATH,
    run_repeatedly_wait_substring,
    timeout,
)


log = get_logger()


def test_project_structure() -> None:
    dirs = {f.name for f in Path().iterdir() if f.is_dir()}
    assert dirs == {"modules", "data", "notebooks"}
    files = {f.name for f in Path().iterdir() if f.is_file()}
    assert files == {
        "Makefile",
        "README.md",
        "LICENSE",
        "apt.txt",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        ".gitignore",
    }


def test_make_help_works() -> None:
    captured = run_once("make help")
    assert not captured.err
    assert captured.out
    assert "setup" in captured.out, f"not found in stdout `{captured.out}`"


def test_make_setup() -> None:
    local_root = Path().resolve()
    apt_deps_result_messages = [f"Setting up {package}" for package in PACKAGES_APT]
    try:
        run_detach_wait_substrings(
            "make setup",
            expect_stdouts=[
                # step 1
                "neuro run ",
                "Status: running",
                # step 2
                f"neuro cp {COOKIECUTTER_APT_FILE_REL_PATH} ",
                f"Copy '{local_root.as_uri()}/{COOKIECUTTER_APT_FILE_REL_PATH}' => ",
                *apt_deps_result_messages,
                # step 3
                f"neuro cp {COOKIECUTTER_PIP_FILE_REL_PATH} ",
                f"Copy '{local_root.as_uri()}/{COOKIECUTTER_PIP_FILE_REL_PATH}' => ",
                "installed pip requirements",
                # step 4
                f"neuro exec setup \"bash -c 'apt-get update ",
                " newly installed,",
            ],
            unexpect_stdouts=["Makefile:", "Status: failed", "recipe for target "],
        )
    except RuntimeError:
        captured = run_once("neuro status setup")
        log.info(f"stdout>{captured.out}")
        log.info(f"stderr>{captured.err}")

    # def test_run_job_fastai(self, neuro_login: None) -> None:
    #     # TODO: fix docs: simplify command (note also issue #66)
    #     # TODO: fix docs: use job name
    #     cmd = (
    #         "neuro run -s cpu-small --http 80 --name=fastai "
    #         "--volume storage://~:/var/storage/home:rw "
    #         "--volume storage://neuromation/public:/var/storage/neuromation/public:ro "
    #         "image://neuromation/fastai"
    #     )
    #     job_name = parse_cli_option(cmd, ("--name", "-n"))
    #
    #     # TODO: define real timeout w.r.t. image size and cluster resources
    #     try:
    #         run_detach(f"neuro kill {job_name}")
    #         with timeout(TIMEOUT_NEURO_JOB_RUN):
    #             with measure_time(f"job-run: {job_name}"):
    #                 run_detach_wait_substring(
    #                     cmd,
    #                     expect_stdout="Status: pending",
    #                     unexpect_stdouts=("Status: failed", "Status: succeeded"),
    #                 )
    #                 run_repeatedly_wait_substring(
    #                     f"neuro status {job_name}", expect_stdout="Status: running"
    #                 )
    #
    #             # TODO: check job's URL
    #     finally:
    #         run_once(f"neuro kill {job_name}")
    #
    # @pytest.mark.flaky(reruns=3)
    # def test_upload_download_dataset(self, neuro_login: None) -> None:
    #     # TODO: fix docs: modify command `neuro cp dataset.tar.gz storage://~`
    #     #  to copy files from folder: `neuro cp -r data/ storage:`
    #     source_local = Path("data/")
    #     target_local = Path("download/")
    #     source_local.mkdir(parents=True, exist_ok=True)
    #     target_local.mkdir(parents=True, exist_ok=True)
    #     cleanup_local_dirs(source_local, target_local)
    #
    #     suffix = f"{N_FILES} x {FILE_SIZE_KB} Kb"
    #     try:
    #         # Upload:
    #         log.info(f"Generating data: {suffix}")
    #         files = [
    #             generate_random_file(source_local, size_b=FILE_SIZE_B)
    #             for _ in range(N_FILES)
    #         ]
    #         files_names = set(str(f.name) for f in files)
    #         with measure_time(f"neuro-cp TO storage, {suffix}"):
    #             captured = run_once("neuro cp -r data/ storage:", TIMEOUT_NEURO_UPLOAD)
    #             assert not captured.err
    #
    #         with measure_time("neuro-ls"):
    #             captured = run_once("neuro ls storage:data/", TIMEOUT_NEURO_STORAGE_LS)
    #             files_uploaded = set(captured.out.split())
    #             assert files_uploaded >= files_names
    #
    #         # Download:
    #         with measure_time(f"neuro-cp FROM storage, {suffix}"):
    #             captured = run_once(
    #                 "neuro cp -r storage:data/ download/", TIMEOUT_NEURO_DOWNLOAD
    #             )
    #             assert not captured.out
    #
    #         files_downloaded = set(str(f.name) for f in target_local.iterdir())
    #         assert files_downloaded >= files_names
    #     finally:
    #         cleanup_local_dirs(source_local, target_local)
    #         with measure_time(f"neuro-rm of the folder, {suffix}"):
    #             run_once("neuro rm -r storage:data", TIMEOUT_NEURO_STORAGE_RM)
