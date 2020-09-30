import subprocess
import typing as t

from cookiecutter.exceptions import FailedHookException

from .conftest import inside_dir


def test_project_tree(cookies: t.Any) -> None:
    result = cookies.bake(extra_context={"project_slug": "test-project"})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project.basename == "test-project"


def test_run_flake8(cookies: t.Any) -> None:
    result = cookies.bake(extra_context={"project_slug": "flake8-compat"})
    with inside_dir(str(result.project)):
        subprocess.check_call(["flake8"])


def test_project_slug_regex_hook(cookies: t.Any) -> None:
    result = cookies.bake(extra_context={"project_slug": "test_project"})
    assert result.exit_code != 0
    assert isinstance(result.exception, FailedHookException)


def test_project_slug_length_hook(cookies: t.Any) -> None:
    result = cookies.bake(extra_context={"project_slug": "t" * 29})
    assert result.exit_code != 0
    assert isinstance(result.exception, FailedHookException)
