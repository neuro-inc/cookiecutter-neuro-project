import logging
import typing as t
from datetime import datetime
from math import floor

from tests.e2e.configuration import LOGFILE_PATH, LOGGER_NAME


TIME_START = datetime.now()


def _timestamp() -> str:
    delta = datetime.now() - TIME_START
    total_sec = delta.total_seconds()
    m = floor(total_sec // 60)
    s = total_sec - m * 60
    return f"{str(m).zfill(2)}:{s:.3f}"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    # TODO: If LOGFILE_PATH is a logger's handler, then it writes pexpect's output
    #  at the end of file, after all log messages. Need to re-write with StreamHandler
    # handler = logging.FileHandler(LOGFILE_PATH, "a", "utf-8")
    # logger.addHandler(handler)
    return logger


LOGGER = get_logger()


def log_msg(msg: str, *, logger: t.Callable[..., None] = LOGGER.info) -> None:
    logger(msg)
    with LOGFILE_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{_timestamp()}: {msg}\n")
        f.flush()
