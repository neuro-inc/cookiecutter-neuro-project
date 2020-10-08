import os
import typing as t
from contextlib import contextmanager


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
