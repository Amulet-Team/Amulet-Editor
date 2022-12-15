"""
This module manages the various python processes.
There is one parent process consisting of the landing page.
All other processes must be direct children of the landing process.
"""

import os
import sys
from enum import Enum
from typing import Callable
from multiprocessing import Process
from . import _messaging


class ProcessType(Enum):
    Null = 0  # The default unset value
    Main = 1  # The main process
    Child = 2  # A child process


def bootstrap(
    process_type: ProcessType,
    main: Callable[..., int],
    *main_args,
    **main_kwargs,
):
    """
    Bootstrap the process.
    This handles setting the process type and launching the main function and exiting when complete.

    :param process_type: The type of process.
    :param main: The main function to call.
    :param main_args: The arguments to pass to main.
    :param main_kwargs: The keyword arguments to pass to main.
    """
    global _process_type
    if not isinstance(process_type, ProcessType):
        raise TypeError("Value must be an enum of ProcessType")
    if _process_type is not ProcessType.Null:
        raise RuntimeError(f"Process {os.getpid()} has already been initialised.")
    if process_type is ProcessType.Null:
        raise ValueError("Cannot set a null process type.")
    _process_type = process_type
    sys.exit(main(*main_args, **main_kwargs))


def bootstrap_process(
    process_type: ProcessType,
    state: _messaging.StateType,
    # Attributes can be added here
    main: Callable[..., int],
    *main_args,
    **main_kwargs,
):
    """
    Bootstrap the new process and call the main function.
    This must only be used from within the spawn function.

    :param process_type: The type of process.
    :param main: The main function to call.
    :param main_args: The arguments to pass to main.
    :param main_kwargs: The keyword arguments to pass to main.
    """
    _messaging.init_state(state)
    # Set module variables here
    bootstrap(process_type, main, *main_args, **main_kwargs)


def spawn(
    process_type: ProcessType,
    main: Callable[..., int],
    *main_args,
    **main_kwargs,
):
    """
    Spawn a new process, set the global state and launch the main function.

    :param process_type: The type of process.
    :param main: The main function to call.
    :param main_args: The arguments to pass to main.
    :param main_kwargs: The keyword arguments to pass to main.
    """
    """Spawn a new process with the given process type."""
    if get_process_type() is not ProcessType.Main:
        raise RuntimeError("Only the main process can spawn new processes.")
    if not isinstance(process_type, ProcessType):
        raise TypeError("Value must be an enum of ProcessType")
    if process_type is ProcessType.Null:
        raise ValueError("Cannot set a null process type.")
    child_process, state = _messaging.get_new_state()
    p = Process(
        target=bootstrap_process,
        args=(
            process_type,
            state,
            # Attributes can be added here
            main,
            *main_args,
        ),
        kwargs=main_kwargs
    )
    child_process.process = p
    p.start()


def get_process_type() -> ProcessType:
    return _process_type
