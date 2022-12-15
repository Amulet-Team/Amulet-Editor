from typing import Optional, NamedTuple, Any
from multiprocessing import Process, Queue
from threading import RLock
from dataclasses import dataclass

from ._process import ProcessType, get_process_type


class FunctionCall(NamedTuple):
    address: str  # The address of the function to call
    args: list[Any]  # The arguments to pass to the function. Must be picklable
    kwargs: dict[str, Any]  # The keyword arguments to pass to the function. Must be picklable


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


StateType = tuple[Queue, Queue]


def init_state(state: StateType):
    """Initialise the state from the parent process."""
    global _parent_down_queue, _parent_up_queue
    parent_down, parent_up = state
    with _lock:
        if _parent_down_queue is None or _parent_down_queue is None:
            raise RuntimeError("Queues have already been set.")
        _parent_down_queue = parent_down
        _parent_up_queue = parent_up


def get_new_state() -> tuple[ChildProcess, StateType]:
    """
    Get the state for the child process.
    The caller must spawn a new process with the returned state and set the process in the child process object.
    """
    global _child_up_queue
    with _lock:
        down = Queue()
        state = ChildProcess(down)
        _child_down_queues.append(state)
        if _child_up_queue is None:
            _child_up_queue = Queue()
        up = _child_up_queue
        return state, (down, up)


def call_down():
    if get_process_type() is ProcessType.Main:
        raise NotImplementedError
    else:
        raise RuntimeError("Can only call down from main process.")


def call_up():
    if get_process_type() is ProcessType.Child:
        raise NotImplementedError
    else:
        raise RuntimeError("Can only call up from child processes.")
