from __future__ import annotations

import logging
from typing import Optional, NamedTuple, Any, Callable, TypeVar
from multiprocessing import Process, Queue
from threading import RLock
from dataclasses import dataclass

from PySide6.QtCore import QThread

from . import _process

log = logging.getLogger(__name__)


CallableT = TypeVar("CallableT", bound=Callable)


class FunctionCall(NamedTuple):
    address: str  # The address of the function to call.
    args: tuple[Any]  # The arguments to pass to the function. Must be picklable.
    kwargs: dict[
        str, Any
    ]  # The keyword arguments to pass to the function. Must be picklable.


@dataclass
class ChildProcess:
    queue: Queue
    process: Optional[Process] = None


# A lock to synchronise everything
_lock = RLock()

# A queue to communicate with the parent process.
# The current process may only write to this queue and only the parent process may read from it.
_parent_up_queue: Optional[Queue] = None

# A queue for the parent process to communicate with the current process.
# Only the parent process may write to this queue and only the current process may read from it.
_parent_down_queue: Optional[Queue] = None

# A list of queues to send data to each child process.
# Only the current process may write to it and only the child process may read from it.
_child_down_queues: list[ChildProcess] = []

# A queue for the child processes to send data to this process.
# Any child process may write to it and only this process may read from it.
_child_up_queue: Optional[Queue] = None

# A map from python function identifier to the function object.
_functions: dict[str, Callable] = {}

_up_thread: Optional[FunctionQueueThread] = None
_down_thread: Optional[FunctionQueueThread] = None


class FunctionQueueThread(QThread):
    def __init__(self, queue: Queue):
        super().__init__()
        self._queue = queue

    def run(self):
        while True:
            call: FunctionCall = self._queue.get()
            try:
                func = _functions[call.address]
            except KeyError:
                log.exception(f"Could not find global function {call.address}")
            else:
                try:
                    func(*call.args, **call.kwargs)
                except Exception as e:
                    log.exception(e)


StateType = tuple[Queue, Queue]


def init_state(state: StateType):
    """Initialise the state from the parent process."""
    global _parent_down_queue, _parent_up_queue, _down_thread
    parent_down, parent_up = state
    with _lock:
        if _parent_down_queue is None or _parent_up_queue is None:
            raise RuntimeError("Queues have already been set.")
        _parent_down_queue = parent_down
        _parent_up_queue = parent_up
        if _down_thread is None:
            _down_thread = FunctionQueueThread(_parent_down_queue)
            _down_thread.start(QThread.LowPriority)


def get_new_state() -> tuple[ChildProcess, StateType]:
    """
    Get the state for the child process.
    The caller must spawn a new process with the returned state and set the process in the child process object.
    """
    global _child_up_queue, _up_thread
    with _lock:
        down = Queue()
        state = ChildProcess(down)
        _child_down_queues.append(state)
        if _child_up_queue is None:
            _child_up_queue = Queue()
        _up_thread = FunctionQueueThread(_child_up_queue)
        _up_thread.start(QThread.LowPriority)
        return state, (down, _child_up_queue)


def get_address(func: CallableT) -> str:
    return f"{func.__module__}.{func.__qualname__}"


def register_global_function(func: CallableT) -> CallableT:
    """
    Register a function to support multiprocess calling.
    Can be used as a decorator.
    """
    address = get_address(func)
    if address in _functions:
        raise RuntimeError(f"Global function {address} was registered twice.")
    else:
        _functions[address] = func
    return func


def call_in_children(func: CallableT, *args, **kwargs):
    if _process.get_process_type() is _process.ProcessType.Main:
        call = FunctionCall(get_address(func), args, kwargs)
        with _lock:
            for queue in _child_down_queues:
                try:
                    queue.queue.put(call)
                except (RuntimeError, ValueError) as e:
                    log.exception(e)
        raise NotImplementedError
    else:
        raise RuntimeError("Can only call down from main process.")


def call_in_parent(func: CallableT, *args, **kwargs):
    if _process.get_process_type() is _process.ProcessType.Child:
        call = FunctionCall(get_address(func), args, kwargs)
        try:
            _parent_up_queue.queue.put(call)
        except (RuntimeError, ValueError) as e:
            log.exception(e)
    else:
        raise RuntimeError("Can only call up from child processes.")
