import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"

_handler = RichHandler(rich_tracebacks=True)
_handler.setFormatter(logging.Formatter(FORMAT, datefmt="[%X]"))

log = logging.getLogger("sync_var")
log.addHandler(_handler)
log.setLevel(logging.WARNING)


def setup_logging(verbose: bool = False) -> None:
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)
