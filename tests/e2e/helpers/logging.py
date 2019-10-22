import logging
import typing as t

# == logging ==
from tests.e2e.configuration import LOGGER_NAME, PEXPECT_DEBUG_OUTPUT_LOGFILE


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    return logger


LOGGER = get_logger()


# == general helpers ==


def log_msg(msg: str, *, logger: t.Callable[..., None] = LOGGER.info) -> None:
    logger(msg)
    PEXPECT_DEBUG_OUTPUT_LOGFILE.write(msg + "\n")
