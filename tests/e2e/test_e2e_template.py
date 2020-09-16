from typing import Any

import pytest
from flaky import flaky

from tests.e2e.configuration import (
    EXISTING_PROJECT_SLUG,
    JOB_STATUS_CANCELLED,
    JOB_STATUS_SUCCEEDED,
    _get_pattern_status_running,
)
from tests.e2e.conftest import (
    STEP_RUN,
    STEP_SETUP,
)
from tests.e2e.helpers.new_runners import run

#
# from tests.e2e.helpers.runners import (
#     finalize,
#     parse_job_id,
#     parse_job_url,
#     repeat_until_success,
#     wait_job_change_status_to,
# )
# from tests.e2e.helpers.utils import measure_time


@pytest.mark.run(order=STEP_SETUP)
@pytest.mark.skipif(
    condition=EXISTING_PROJECT_SLUG is not None and len(EXISTING_PROJECT_SLUG) > 0,
    reason="Reusing existing project, no need to run setup",
)
def test_make_setup_full() -> None:
    try:
        run("neuro-flow mkvolumes")
        run("neuro-flow upload ALL")
        run("neuro-flow build myimage")
    except Exception as e:
        pytest.exit(f"Setup test failed, aborting the whole test suite. Error: {e}")



# @pytest.mark.run(order=STEP_RUN)
# def test_make_train_defaults(monkeypatch: Any, env_var_preset_cpu_small: None) -> None:
#     monkeypatch.setenv("RUN_EXTRA", "--detach")
#     with finalize("neuro-flow kill train"):
#         out = run(
#             "neuro-flow run train", expect_patterns=["Your training script here"],
#         )
#         job_id = parse_job_id(out)
#         wait_job_change_status_to(job_id, JOB_STATUS_SUCCEEDED)
#
#
# @pytest.mark.run(order=STEP_RUN)
# def test_make_run_jupyter_notebook(env_var_no_http_auth: None) -> None:
#     _test_run_something_useful("jupyter", "/tree")
#
#
# @pytest.mark.run(order=STEP_RUN)
# def test_make_jupyter_lab(env_var_no_http_auth: None,) -> None:
#     _test_run_something_useful("jupyter", "/lab")
#
#
# @pytest.mark.run(order=STEP_RUN)
# def test_make_tensorboard(env_var_no_http_auth: None) -> None:
#     _test_run_something_useful("tensorboard", "/")
#
#
# def _test_run_something_useful(target: str, path: str) -> None:
#     with finalize(f"neuro-flow kill {target}"):
#         cmd = f"neuro-flow run {target}"
#         with measure_time(cmd):
#             out = run(
#                 cmd,
#                 expect_patterns=[_get_pattern_status_running()],
#                 assert_exit_code=False,
#             )
#
#         job_id = parse_job_id(out)
#         url = parse_job_url(run(f"neuro status {job_id}"))
#         repeat_until_success(
#             f"curl --fail {url}{path}",
#             job_id,
#             expect_patterns=[r"<[^>]*html.*>"],
#             error_patterns=["curl: .+"],
#             verbose=False,
#             assert_exit_code=False,
#         )
#
#         run(f"neuro-flow kill {target}")
#         wait_job_change_status_to(job_id, JOB_STATUS_CANCELLED)
#
#
# @pytest.mark.run(order=STEP_RUN)
# def test_make_develop() -> None:
#     target = "develop"
#     with finalize(f"neuro-flow kill {target}"):
#         cmd = f"neuro-flow run {target}"
#         with measure_time(cmd):
#             run(cmd, expect_patterns=[_get_pattern_status_running()])
#         run("neuro-flow kill develop")
#
#
# @pytest.mark.run(order=STEP_RUN)
# @pytest.mark.timeout(5 * 60)
# @flaky(max_runs=3)
# @pytest.mark.skipif(
#     sys.platform == "win32", reason="FIXME: Incorrect secret path on Windows"
# )
# def test_gsutil_auth_works_from_python_api(
#     gcp_secret_mount: None, env_var_preset_cpu_small: None, monkeypatch: Any
# ) -> None:
#     # TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
#     monkeypatch.setenv("SECRETS", gcp_secret_mount)
#
#     script_path = f"{MK_CODE_DIR}/train.py"
#     script = Path(script_path)
#     script.write_text(
#         textwrap.dedent(
#             """
#             from google.cloud import storage
#             bucket = storage.Client().get_bucket("cookiecutter-e2e")
#             print(bucket.get_blob("hello.txt").download_as_string())
#             """
#         )
#     )
#     run("make upload-code")
#
#     target = "train"
#
#     make_cmd = f'neuro-flow run train TRAIN_CMD="python {script_path}"'
#     with finalize(f"neuro-flow kill {target}"):
#         with measure_time(make_cmd):
#             out = run(make_cmd)
#
#         job_id = parse_job_id(out)
#
#         cmd = f"neuro logs {job_id}"
#         with measure_time(cmd):
#             run(
#                 cmd,
#                 expect_patterns=["Hello world!"],
#                 error_patterns=["Errno", "No such file or directory"],
#             )
