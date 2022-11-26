"""
This module manages the various python processes.
There is one parent process consisting of the landing page.
All other processes must be direct children of the landing process.
"""

import os
import sys
from enum import Enum
import amulet_editor.application._app as app


class ProcessType(Enum):
    Null = 0  # The default unset value
    Home = 1  # The landing parent process
    Level = 2  # A child process that owns one level


_process_type = ProcessType.Null


def init(process_type: ProcessType):
    """
    Initialise the process.
    If spawning a new process this function must be called as the input function.
    """
    global _process_type
    if not isinstance(process_type, ProcessType):
        raise TypeError("Value must be an enum of ProcessType")

    if _process_type is ProcessType.Null:
        _process_type = process_type
        if process_type is ProcessType.Null:
            raise ValueError("Cannot set a null process type.")
        elif process_type is ProcessType.Home:
            sys.exit(app.AmuletEditorStartupApp().exec())
        elif process_type is ProcessType.Level:
            sys.exit(app.AmuletEditorLevelApp().exec())
    else:
        raise RuntimeError(f"Process {os.getpid()} has already been initialised.")


def spawn(process_type: ProcessType):
    """Spawn a new process with the given process type."""
    if process_type is ProcessType.Level:
        raise NotImplementedError
    else:
        raise ValueError(f"Cannot launch new process of type {process_type}")


def call_up():
    if _process_type is ProcessType.Level:
        raise NotImplementedError
    else:
        raise RuntimeError("Can only call up from child processes.")


def call_down():
    if _process_type is ProcessType.Home:
        raise NotImplementedError
    else:
        raise RuntimeError("Can only call down from main process.")
