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
def measure_time(cmd: str) -> t.Iterator[None]:
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        msg = f"Time summary [{cmd}]: {elapsed:.2f} sec"
        log_msg("-" * len(msg), logger=LOGGER.info)


@contextmanager
def retry(attempts: int, callable: t.Callable[[], t.Any]) -> t.Any:
    for attempt in range(1, attempts + 1):
        try:
            return callable()
        except BaseException as e:
            log_msg(f"Attempt {attempt}: Caught error {e}")
            if attempt == attempts:
                log_msg("Giving up.")
                raise
