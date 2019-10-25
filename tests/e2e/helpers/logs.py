import logging
import typing as t
from datetime import datetime
from math import floor

from tests.e2e.configuration import CI, LOGGER_NAME, PEXPECT_DEBUG_OUTPUT_LOGFILE


TIME_START = datetime.now()


def _timestamp() -> str:
    delta = datetime.now() - TIME_START
    total_sec = delta.total_seconds()
    m = floor(total_sec // 60)
    s = total_sec - m * 60
    return f"{str(m).zfill(2)}:{s:.3f}"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    return logger


LOGGER = get_logger()


def log_msg(msg: str, *, logger: t.Callable[..., None] = LOGGER.info) -> None:
    logger(msg)
    if CI:
        PEXPECT_DEBUG_OUTPUT_LOGFILE.write(f"{_timestamp()}: " + msg + "\n")
