import logging
import traceback as tb
from amulet_editor.application._invoke import invoke
from ._cls import _AmuletTracebackDialog


def display_exception_blocking(title: str = "", error: str = "", traceback: str = ""):
    """
    Display an exception window.
    This must be called from the main thread.
    This blocks until the user closes the window.

    :param title: The title of the dialog.
    :param error: A user-readable description of the error context.
    :param traceback: The traceback to display in the dialog.
    """
    dialog = _AmuletTracebackDialog(title=title, error=error, traceback=traceback)
    dialog.exec()


def display_exception(title: str = "", error: str = "", traceback: str = ""):
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


class DisplayException:
    """
    A context manager class to display the traceback dialog when an error occurs.
    It will also log the exception to the logging module and optionally suppress the exception.
    """

    def __init__(self, msg: str, *, suppress=False, log=logging.getLogger()):
        self._msg = msg
        self._suppress = suppress
        self._log = log

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and isinstance(exc_val, Exception):
            self._log.exception(exc_val)
            display_exception(
                title=self._msg,
                error=str(exc_val),
                traceback="".join(tb.format_tb(exc_tb)),
            )
            return self._suppress
        return False
