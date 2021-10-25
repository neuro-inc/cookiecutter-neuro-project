import sys

import pytest
from pytest_cookies.plugin import Cookies  # type: ignore

from tests.e2e.conftest import exec
from tests.utils import inside_dir


# Also check whether comments and their removal does not break something
@pytest.mark.parametrize("preserve_comments", ["yes", "no"])
def test_neuro_flow_live(cookies: Cookies, preserve_comments: str) -> None:
    result = cookies.bake(
        extra_context={
            "project_dir": "test-project",
            "project_id": "awesome_project",
            "preserve Neuro Flow template hints": preserve_comments,
        }
    )
    with inside_dir(str(result.project_path)):
        proc = exec("neuro-flow --show-traceback ps")
        assert not proc.stderr, proc
        assert "JOB" in proc.stdout, proc

        proc = exec("neuro-flow --show-traceback status train", assert_exit_code=False)
        # https://github.com/neuro-inc/neuro-flow/issues/331
        assert not proc.stderr or sys.platform == "win32", proc
        assert "is not running" in proc.stdout, proc

        proc = exec("neuro-flow --show-traceback run --dry-run train")
        assert not proc.stderr, proc
        assert "neuro run" in proc.stdout, proc
        assert "--tag=project:awesome-project" in proc.stdout, proc

        proc = exec("neuro-flow --show-traceback run --dry-run remote_debug")
        assert not proc.stderr, proc
        assert "neuro run" in proc.stdout, proc
        assert "--tag=project:awesome-project" in proc.stdout, proc
