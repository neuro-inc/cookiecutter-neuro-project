import os
import subprocess
import typing as t
from contextlib import contextmanager
from tests.utils import inside_dir

@contextmanager
def inside_dir(dirpath: str) -> t.Iterator[None]:
    """
    Execute code from inside the given directory
    :param dirpath: String, path of the directory the command is being run.
    """
    old_path = os.getcwd()
    try:
        os.chdir(dirpath)
        yield
    finally:
        os.chdir(old_path)


def test_project_tree(cookies: t.Any) -> None:
    result = cookies.bake(extra_context={"project_slug": "test_project"})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project.basename == "test_project"


def test_run_flake8(cookies: t.Any) -> None:
    result = cookies.bake(extra_context={"project_slug": "flake8_compat"})
    with inside_dir(str(result.project)):
        subprocess.check_call(["flake8"])
