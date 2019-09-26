import logging
import signal
import time
import typing as t
from contextlib import contextmanager
from uuid import uuid4


LOGGER_NAME = "e2e"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    return logger


log = get_logger()


def unique_label() -> str:
    return uuid4().hex[:8]


@contextmanager
def timeout(time_s: int) -> t.Iterator[None]:
    """ source: https://www.jujens.eu/posts/en/2018/Jun/02/python-timeout-function/
    """

    def raise_timeout(signum: int, frame: t.Any) -> t.NoReturn:
        raise TimeoutError

    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time_s)

    try:
        yield
    except TimeoutError:
        log.error(f"TIMEOUT ERROR: {time_s}")
        raise
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


@contextmanager
def measure_time(command_name: str = "") -> t.Iterator[None]:
    log.info("-" * 50)
    start_time = time.time()
    log.info(f"Measuring time for command: `{command_name}`")
    yield
    elapsed_time = time.time() - start_time
    log.info("=" * 50)
    log.info(f"  TIME SUMMARY [{command_name}]: {elapsed_time:.2f} sec")
    log.info("=" * 50)
