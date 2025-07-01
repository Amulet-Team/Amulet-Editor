"""
Launch commands that can be executed through the CLI.
Plugins can register their own launch commands.
"""

import argparse
from typing import Any
from weakref import WeakSet
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class Command:
    name: str
    main_func: Callable[[Any], None]
    init_argparse: Callable[[argparse.ArgumentParser], None] | None = None


_lock = Lock()
_commands = WeakSet[Command]()


def register_command(command: Command) -> None:
    if not isinstance(command, Command):
        raise TypeError(f"Command {command} is not a Command")
    with _lock:
        if any(c.name == command.name for c in _commands):
            raise RuntimeError(f"Command {command.name} has already been registered.")
        _commands.add(command)


def unregister_command(command: Command) -> None:
    if not isinstance(command, Command):
        raise TypeError(f"Command {command} is not a Command")
    with _lock:
        if command in _commands:
            _commands.remove(command)
