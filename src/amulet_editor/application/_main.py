from __future__ import annotations

import threading
from typing import Optional, Callable, TypeAlias, Any, Union
from types import FrameType
import sys
import os
import logging
from datetime import datetime
import faulthandler
from io import TextIOWrapper
import atexit

from PySide6.QtCore import (
    Qt,
    QCoreApplication,
    qInstallMessageHandler,
    QtMsgType,
    QLocale,
    QMessageLogContext,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat

from amulet.level import get_level
import amulet_editor
from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet_editor.data.level import _level
from amulet_editor.models.localisation import ATranslator
import amulet_editor.data._rpc as rpc

from ._cli import parse_args, BROKER
from ._app import AmuletApp
from amulet_editor.data.paths._application import _init_paths, logging_directory

TraceFunction: TypeAlias = Callable[[FrameType, str, Any], Union["TraceFunction", None]]

log = logging.getLogger(__name__)
qt_log = logging.getLogger("Qt")


def _qt_log(msg_type: QtMsgType, context: QMessageLogContext, msg: str) -> None:
    if msg_type == QtMsgType.QtDebugMsg:
        qt_log.debug(msg)
    if msg_type == QtMsgType.QtInfoMsg:
        qt_log.info(msg)
    if msg_type == QtMsgType.QtWarningMsg:
        qt_log.warning(msg)
    if msg_type == QtMsgType.QtCriticalMsg:
        qt_log.critical(msg)
    if msg_type == QtMsgType.QtFatalMsg:
        qt_log.fatal(msg)


def app_main() -> None:
    args = parse_args()
    _init_paths(args.data_dir, args.config_dir, args.cache_dir, args.log_dir)

    log_file = open(
        os.path.join(
            logging_directory(),
            f"amulet-log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{os.getpid()}.txt",
        ),
        "w",
    )

    logging.basicConfig(
        level=args.logging_level,
        format=args.logging_format,
        force=True,
        handlers=[
            logging.StreamHandler(sys.__stderr__),
            logging.StreamHandler(log_file),
        ],
    )
    # TODO: remove old log files

    class StdCapture(TextIOWrapper):
        def __init__(self, logger: Callable[[str], None]) -> None:
            super().__init__(log_file)  # type: ignore
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

    # When running via pythonw the stderr is None so log directly to the log file
    faulthandler.enable(sys.__stderr__ or log_file)

    if args.trace:

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

    is_broker = args.level_path == BROKER

    if is_broker:
        # Dummy application to get a main loop.
        app = QApplication()
        translator = ATranslator()
        translator.load_lang(
            QLocale(),
            "",
            directory=os.path.join(*amulet_editor.__path__, "resources", "lang"),
        )
        QCoreApplication.installTranslator(translator)
    else:
        # # Allow context sharing between widgets that do not share the same top level window.
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

        # # Set the default surface format. Apparently this is required for some platforms.
        surface_format = QSurfaceFormat()
        surface_format.setDepthBufferSize(24)
        surface_format.setVersion(3, 2)
        surface_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        QSurfaceFormat.setDefaultFormat(surface_format)

        app = AmuletApp()
        # The broker cannot have a level
        level_path: Optional[str] = args.level_path
        if level_path is None:
            _level.level = None
        else:
            log.debug("Loading level.")
            with DisplayException(f"Failed loading level at path {level_path}"):
                _level.level = level = get_level(level_path)
                level.open()

    # rpc.init_rpc(is_broker)

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)
