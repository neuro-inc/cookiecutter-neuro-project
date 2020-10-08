import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union


@contextmanager
def inside_dir(dirpath: Union[str, Path]) -> Iterator[None]:
    """
    Execute code from inside the given directory
    :param dirpath: String, path of the directory the command is being run.
    """
    old_path = os.getcwd()
    try:
        os.chdir(str(dirpath))
        yield
    finally:
        os.chdir(old_path)
