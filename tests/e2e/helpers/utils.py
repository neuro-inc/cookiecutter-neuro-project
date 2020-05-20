import os
import shutil
import time
import typing as t
from contextlib import contextmanager
from pathlib import Path

from tests.e2e.configuration import unique_label
from tests.e2e.helpers.logs import LOGGER, log_msg


# == local file helpers ==


def generate_random_file(path: Path, size_b: int) -> Path:
    name = f"{unique_label()}.tmp"
    path_and_name = path / name
    with path_and_name.open("wb") as file:
        generated = 0
        while generated < size_b:
            length = min(1024 * 1024, size_b - generated)
            data = os.urandom(length)
            file.write(data)
            generated += len(data)
    return path_and_name


def cleanup_local_dirs(*dirs: t.Union[str, Path]) -> None:
    for d_or_name in dirs:
        if isinstance(d_or_name, str):
            d = Path(d_or_name)
        else:
            d = d_or_name
        log_msg(f"Cleaning up local directory `{d.absolute()}`")
        assert d.is_dir(), f"not a dir: {d}"
        assert d.exists(), f"not exists before cleanup: {d}"
        for f in d.iterdir():
            if f.is_file():
                f.unlink()
        assert d.exists(), f"not exists after cleanup: {d}"
        ls = list(d.iterdir())
        assert not ls, f"directory should be empty here: {ls}"


def copy_local_files(from_dir: Path, to_dir: Path) -> None:
    for f in from_dir.glob("*"):
        if not f.is_file():
            continue
        target = to_dir / f.name
        if target.exists():
            log_msg(f"Target `{target.absolute()}` already exists")
            continue
        log_msg(f"Copying file `{f}` to `{target.absolute()}`")
        shutil.copyfile(str(f), target, follow_symlinks=False)


# == helpers ==


@contextmanager
def measure_time(cmd: str, timeout: float = 0.0) -> t.Iterator[None]:
    """
    >>> t_0 = time.time()
    >>> try:
    ...     with measure_time("sleep", timeout=0.01):
    ...         time.sleep(0.1)
    ...     #assert False, "should not be here"
    ...     # TODO (ayushkovskiy) Unignore the assert above once #333 is resolved
    ... except TimeoutError as e:
    ...     assert str(e) == "Time summary [sleep]: 0.10 sec (timeout: 0.01 sec)", e
    >>> elapsed = time.time() - t_0
    >>> assert elapsed >= 0.1
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        msg = f"Time summary [{cmd}]: {elapsed:.2f} sec (timeout: {timeout:.2f} sec)"
        exceeded = 0 < timeout < elapsed
        logger = LOGGER.info if not exceeded else LOGGER.error
        log_msg("-" * len(msg), logger=logger)

        if exceeded:
            # TODO (ayushkovskiy) Once issue #333 is resolved, raise TimeoutError again.
            #   Also, don't forget to unignore the doctest for this function.
            # raise TimeoutError(msg)
            log_msg(
                f"WARNING: Temporarily ignoring timeout error, see issue #333",
                logger=LOGGER.warning,
            )


def merge_similars(collection: t.Iterable[str]) -> t.Iterable[str]:
    """
    >>> list(merge_similars("a b b c c c d d e".split()))
    ['a', 'b', 'c', 'd', 'e']
    >>> list(merge_similars("a b b c c c d d e e".split()))
    ['a', 'b', 'c', 'd', 'e']
    """
    prev: t.Optional[str] = None
    for el in collection:
        assert isinstance(el, str), f"expected 'str', got {type(el)}"
        if el != prev:
            yield el
        prev = el
