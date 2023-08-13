# This module manages the console output

from io import TextIOWrapper

import logging
import sys


def init_console():
    stderr = sys.stderr

    # Set up a default logging configuration until it is configured properly later.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s - %(message)s",
        force=True,
        handlers=[
            logging.StreamHandler(stderr)
        ]
    )
    logging.getLogger().setLevel(logging.WARNING)

    class StdCapture(TextIOWrapper):
        def __init__(self, logger):
            super().__init__(stderr.buffer)
            self._logger = logger

        def write(self, msg):
            if msg != "\n":
                self._logger(msg)

    # Convert all direct stdout calls (eg print) to info log calls
    sys.stdout = StdCapture(logging.getLogger("Python stdout").info)
    # Convert all direct stderr calls (eg warnings and errors) to error log calls
    sys.stderr = StdCapture(logging.getLogger("Python stderr").error)

    # Handle the qt output in a more useful way
    from PySide6.QtCore import qInstallMessageHandler, QtMsgType

    qt_log = logging.getLogger("Qt")

    def _qt_log(msg_type, context, msg):
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

    qInstallMessageHandler(_qt_log)
