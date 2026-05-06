"""
Launch commands that can be executed through the CLI.
Plugins can register their own launch commands.
"""

from __future__ import annotations
from typing import NoReturn
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
import sys


@dataclass(frozen=True, kw_only=True)
class Command:
    name: str
    main: Callable[[list[str]], NoReturn]


_lock = Lock()
_commands = dict[str, Command]()


def register_command(command: Command) -> None:
    """Register a command. The name must be unique."""
    if not isinstance(command, Command):
        raise TypeError(f"Command {command} is not a Command")
    with _lock:
        if command.name in _commands:
            raise RuntimeError(f"Command {command.name} has already been registered.")
        _commands[command.name] = command


def get_commands() -> list[str]:
    """Get the list of command strings."""
    with _lock:
        return list(_commands)


def run_command(name: str, args: list[str]) -> NoReturn:
    with _lock:
        command = _commands.get(name)
    if command is None:
        raise RuntimeError(f'Could not find the "{name}" command.')
    command.main(args)
    sys.exit(0)
