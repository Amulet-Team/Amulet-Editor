from __future__ import annotations

import threading
from typing import Optional
import sys
import os
import logging
from datetime import datetime

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat

import amulet
from amulet_editor.models.widgets.traceback_dialog import DisplayException
from amulet_editor.data.project import _level
import amulet_editor.data._rpc as rpc

from ._cli import parse_args, Args, BROKER
from ._app import AmuletApp
from amulet_editor.data.paths._application import _init_paths, logging_directory

log = logging.getLogger(__name__)


def _init_logging(args: Args):
    logging.basicConfig(
        level=args.logging_level, format=args.logging_format, force=True
    )
    file_path = os.path.join(
        logging_directory(),
        f"amulet-log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{os.getpid()}.txt",
    )
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(logging.Formatter(args.logging_format))
    logging.getLogger().addHandler(file_handler)
    # TODO: remove old log files


def app_main():
    args = parse_args()
    _init_paths(args.data_dir, args.config_dir, args.cache_dir, args.log_dir)
    _init_logging(args)

    if args.trace:

        def trace_calls(frame, event, arg):
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
    rpc.init_rpc(is_broker)

    if is_broker:
        # Dummy application to get a main loop.
        app = QApplication()
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
                _level.level = amulet.load_level(level_path)

    log.debug("Entering main loop.")
    exit_code = app.exec()
    log.debug(f"Exiting with code {exit_code}")
    sys.exit(exit_code)
