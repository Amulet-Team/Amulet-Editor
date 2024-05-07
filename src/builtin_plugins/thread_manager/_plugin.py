import logging

from shiboken6 import isValid
from PySide6.QtCore import QThread

from amulet_editor.models.plugin import PluginV1

log = logging.getLogger(__name__)

_threads: set[tuple[str, QThread]] = set()


def new_thread(name: str) -> QThread:
    """
    Get a new QThread instance.
    When you are done with the thread you should quit and delete it.
    This plugin will handle waiting for the thread to finish so that the application does not crash.
    """
    thread = QThread()
    thread.setObjectName(name)
    storage = name, thread
    _threads.add(storage)
    thread.finished.connect(lambda: _threads.remove(storage))
    return thread


def unload_plugin() -> None:
    threads = tuple(_threads)

    # Quit all threads.
    # These will run concurrently.
    for thread_name, thread in threads:
        if isValid(thread):
            log.debug(f"Quitting thread {thread_name}. {thread}")
            thread.quit()

    # Wait for all the threads to finish
    for thread_name, thread in threads:
        if isValid(thread):
            log.debug(f"Waiting for thread {thread_name}. {thread}")
            thread.wait()


plugin = PluginV1(unload=unload_plugin)
