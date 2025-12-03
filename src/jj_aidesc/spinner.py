import logging
from functools import partial
from typing import Type, Union

from halo import Halo

log = logging.getLogger(__name__)


class LogSpinner:
    """Halo-compatible spinner that uses logging for verbose mode."""

    def __init__(self, text: str = "", **kwargs) -> None:
        """Initialize and log the starting message."""
        self.text = text
        if text:
            log.info(text)

    def __enter__(self) -> "LogSpinner":
        return self

    def __exit__(self, *args) -> None:
        pass

    def succeed(self, text: str = "") -> None:
        """Log success message."""
        log.info(f"✔ {text or self.text}")

    def fail(self, text: str = "") -> None:
        """Log failure message."""
        log.error(f"✖ {text or self.text}")

    def warn(self, text: str = "") -> None:
        """Log warning message."""
        log.warning(f"⚠ {text or self.text}")

    def info(self, text: str = "") -> None:
        """Log info message."""
        log.info(f"ℹ {text or self.text}")

    def stop(self) -> None:
        """No-op for compatibility."""
        pass

    def start(self) -> None:
        """No-op for compatibility."""
        pass


def get_spinner(verbose: bool) -> Union[Type[LogSpinner], partial]:
    """Get spinner class based on verbose mode.

    Args:
        verbose: If True, return LogSpinner (just logs), otherwise return Halo

    Returns:
        Spinner class or partial
    """
    if verbose:
        return LogSpinner
    return partial(Halo, spinner="dots")
