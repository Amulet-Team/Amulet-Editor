from types import TracebackType
import logging
import traceback as tb
from amulet.app.invoke import invoke
from ._traceback_dialog import TracebackDialog

main_logger = logging.getLogger()


def display_exception_blocking(
    title: str = "", error: str = "", traceback: str = ""
) -> None:
    """
    Display an exception window.
    This must be called from the main thread.
    This blocks until the user closes the window.

    :param title: The title of the dialog.
    :param error: A user-readable description of the error context.
    :param traceback: The traceback to display in the dialog.
    """
    dialog = TracebackDialog(title=title, error=error, traceback=traceback)
    dialog.exec()


def display_exception(title: str = "", error: str = "", traceback: str = "") -> None:
    """
    Display an exception window.
    This is processed when control returns to the main thread.
    This is thread safe.

    :param title: The title of the dialog.
    :param error: A user-readable description of the error context.
    :param traceback: The traceback to display in the dialog.
    """
    invoke(
        lambda: display_exception_blocking(
            title=title, error=error, traceback=traceback
        )
    )


class CatchExceptionDialog:
    """
    A context manager to catch, log, display and optionally suppress exceptions.
    """
    def __init__(
        self,
        msg: str,
        *,
        exception_class: type[BaseException] = Exception,
        suppress: bool = True,
        logger: logging.Logger | None = logging.getLogger(),
    ) -> None:
        self._msg = msg
        if not issubclass(exception_class, BaseException):
            raise TypeError(f"{exception_class!r} is not a sub-class of BaseException.")
        self._exception_class = exception_class
        self._suppress = suppress
        self._logger = logger

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type and isinstance(exc_val, self._exception_class):
            if self._logger is not None:
                self._logger.exception(exc_val)
            display_exception(
                title=self._msg,
                error=str(exc_val),
                traceback="".join(tb.format_tb(exc_tb)),
            )
            return self._suppress
        return False
