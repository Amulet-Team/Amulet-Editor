from __future__ import annotations

import threading
from typing import Callable, TypeAlias, Any, Union
from types import FrameType, TracebackType
from collections.abc import Sequence
from threading import ExceptHookArgs
import sys
import os
import logging
from datetime import datetime
import faulthandler
from io import TextIOBase
import atexit
import traceback

from PySide6.QtCore import (
    qInstallMessageHandler,
    QtMsgType,
    QMessageLogContext,
)

import amulet.utils.logging

import amulet.app.plugin._manager as plugin_manager

from amulet.app.cli._parser import parse_cli
from amulet.app.cli._command import get_commands, run_command
from amulet.app.path._application import init_paths, logging_directory
from amulet.app.exception import display_exception

TraceFunction: TypeAlias = Callable[[FrameType, str, Any], Union["TraceFunction", None]]

log = logging.getLogger(__name__)
qt_log = logging.getLogger("Qt")


def _qt_log(msg_type: QtMsgType, context: QMessageLogContext, msg: str) -> None:
    if msg_type == QtMsgType.QtDebugMsg:
        qt_log.debug(msg)
    elif msg_type == QtMsgType.QtInfoMsg:
        qt_log.info(msg)
    elif msg_type == QtMsgType.QtWarningMsg:
        qt_log.warning(msg)
    elif msg_type == QtMsgType.QtCriticalMsg:
        qt_log.critical(msg)
    elif msg_type == QtMsgType.QtFatalMsg:
        qt_log.fatal(msg)


def app_main(argv: Sequence[str] | None = None) -> None:
    # Set up global state.
    # Plugins have not been loaded at this point.
    cli_args = parse_cli(argv)
    init_paths(
        cli_args.data_dir,
        cli_args.config_dir,
        cli_args.cache_dir,
        cli_args.log_dir,
    )

    log_file = open(
        os.path.join(
            logging_directory(),
            f"amulet-log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{os.getpid()}.txt",
        ),
        "w",
    )

    logging.basicConfig(
        level=cli_args.logging_level,
        format=cli_args.logging_format,
        force=True,
        handlers=[
            logging.StreamHandler(sys.__stderr__),
            logging.StreamHandler(log_file),
        ],
    )
    logging.getLogger("OpenGL.acceleratesupport").setLevel(logging.CRITICAL)
    # TODO: remove old log files

    class StdCapture(TextIOBase):
        def __init__(self, logger: Callable[[str], None]) -> None:
            super().__init__()
            self._logger = logger

        def write(self, msg: str) -> int:
            msg = msg.rstrip()
            if msg:
                self._logger(msg)
                return len(msg)
            return 0

    # Convert all direct stdout calls (eg print) to info log calls
    sys.stdout = StdCapture(logging.getLogger("Python stdout").info)
    # Convert all direct stderr calls (eg warnings and errors) to error log calls
    sys.stderr = StdCapture(logging.getLogger("Python stderr").error)

    # Handle the qt output in a more useful way
    qInstallMessageHandler(_qt_log)

    # If qt calls the message handler after the python interpreter has shut down it will crash.
    # Uninstall the message handler at interpreter shutdown so it can't get called.
    # This means that any errors after interpreter shutdown are not logged. TODO is there a way to handle this?
    atexit.register(lambda: qInstallMessageHandler(None))

    def error_handler(
        exc_type: type[BaseException],
        exc_value: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_value is None:
            return
        log.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        display_exception(
            "Unhandled exception",
            "",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )

    sys.excepthook = error_handler

    def thread_error_handler(exc: ExceptHookArgs) -> None:
        error_handler(exc.exc_type, exc.exc_value, exc.exc_traceback)

    threading.excepthook = thread_error_handler

    # Link the Amulet C++ logging
    amulet.utils.logging.set_min_log_level(cli_args.logging_level)

    # When running via pythonw the stderr is None so log directly to the log file
    faulthandler.enable(sys.__stderr__ or log_file)

    if cli_args.trace:

        def trace_calls(frame: FrameType, event: str, arg: Any) -> TraceFunction:
            if event == "call":
                try:
                    qual_name = frame.f_code.co_qualname
                    module_name = frame.f_globals["__name__"]
                    logging.info(f"Call to {module_name}.{qual_name}")
                except AttributeError:
                    pass
            return trace_calls

        sys.settrace(trace_calls)
        threading.settrace(trace_calls)

    # Load the plugins so they can register entry points
    plugin_manager.load()

    # Validate the command and show help if requested.
    valid_commands = get_commands()
    if cli_args.help or cli_args.command not in valid_commands:
        parse_cli(argv, valid_commands)

    # Call the requested command
    run_command(cli_args.command, cli_args.args)
