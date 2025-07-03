from __future__ import annotations

import threading
from typing import Callable, TypeAlias, Any, Union
from types import FrameType
from collections.abc import Sequence
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
    QTimer,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat

from amulet.app.resource import get_resource_path
from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet.app.localisation import Translator, locale_changed
import amulet.app.plugin._manager as plugin_manager
import amulet_editor.data._rpc as rpc

from amulet.app.cli._parser import parse_global_args, parse_args
from amulet.app.cli._command import run_command
from amulet.app.path._application import init_paths, logging_directory

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
    global_args = parse_global_args(argv)
    init_paths(
        global_args.data_dir,
        global_args.config_dir,
        global_args.cache_dir,
        global_args.log_dir,
    )

    log_file = open(
        os.path.join(
            logging_directory(),
            f"amulet-log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{os.getpid()}.txt",
        ),
        "w",
    )

    logging.basicConfig(
        level=global_args.logging_level,
        format=global_args.logging_format,
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

    if global_args.trace:

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

    if QApplication.instance() is not None:
        raise RuntimeError("QApplication has already been initialized")

    # Allow context sharing between widgets that do not share the same top level window.
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    # Set the default surface format. Apparently this is required for some platforms.
    surface_format = QSurfaceFormat()
    surface_format.setDepthBufferSize(24)
    surface_format.setVersion(3, 2)
    surface_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(surface_format)
    app = QApplication()

    translator = Translator()

    def load_translations() -> None:
        translator.load_lang(
            QLocale(),
            "",
            directory=get_resource_path("lang"),
        )

    load_translations()
    QApplication.installTranslator(translator)
    locale_changed.connect(load_translations)

    def shut_down() -> None:
        plugin_manager.unload()

    app.aboutToQuit.connect(shut_down)

    def launch() -> None:
        with DisplayException("Failed to launch"):
            plugin_manager.load()
            full_args = parse_args(argv)
            run_command(full_args.command or "main", full_args)

    # This will be processed after the app starts
    QTimer.singleShot(0, launch)

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)

    # is_broker = global_args.level_path == BROKER
    #
    # if is_broker:
    #     # Dummy application to get a main loop.
    #     app = QApplication()
    #     translator = Translator()
    #     translator.load_lang(
    #         QLocale(),
    #         "",
    #         directory=get_resource_path("lang"),
    #     )
    #     QCoreApplication.installTranslator(translator)
    #
    # # rpc.init_rpc(is_broker)
