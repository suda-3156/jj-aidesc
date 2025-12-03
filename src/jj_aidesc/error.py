"""Error handling utilities."""

import sys
from functools import wraps
from typing import Callable, TypeVar

from rich.console import Console

console = Console(highlight=False)

F = TypeVar("F", bound=Callable)


class JJAIDescError(Exception):
    """Base exception for jj-aidesc."""

    pass


class ConfigError(JJAIDescError):
    """Configuration error."""

    pass


class JJError(JJAIDescError):
    """JJ command error."""

    pass


class AIError(JJAIDescError):
    """AI generation error."""

    pass


class AbortError(JJAIDescError):
    """User abort error."""

    pass


def error_handle(func: F) -> F:
    """Decorator for handling errors in CLI commands."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AbortError as e:
            console.print(f"[yellow]Aborted:[/yellow] {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            sys.exit(130)
        except JJAIDescError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]Unexpected error:[/bold red] {e}")
            sys.exit(1)

    return wrapper  # type: ignore
