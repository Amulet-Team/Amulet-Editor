"""
Launch commands that can be executed through the CLI.
Plugins can register their own launch commands.
"""

from __future__ import annotations
from argparse import ArgumentParser
from typing import Any, TYPE_CHECKING
from weakref import WeakSet, WeakValueDictionary
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from threading import Lock
from types import MappingProxyType

from ._parser import FullArgs


@dataclass(frozen=True, kw_only=True)
class Command:
    name: str
    main_func: Callable[[FullArgs], None]
    init_argparse: Callable[[ArgumentParser], None] | None = None
    add_parser_args: Sequence[Any] = ()
    add_parser_kwargs: Mapping[str, Any] = MappingProxyType({})

    def __hash__(self) -> int:
        return id(self)


_lock = Lock()
_commands_set = WeakSet[Command]()
_commands_map = WeakValueDictionary[str, Command]()


def register_command(command: Command) -> None:
    """
    Register a command. The name must be unique.
    The Command object must be kept alive by the caller.
    """
    if not isinstance(command, Command):
        raise TypeError(f"Command {command} is not a Command")
    with _lock:
        if command.name in _commands_map:
            raise RuntimeError(f"Command {command.name} has already been registered.")
        _commands_set.add(command)
        _commands_map[command.name] = command


def unregister_command(command: Command) -> None:
    """
    Unregister a command.
    If the Command object was not previously registered, this will do nothing.
    """
    if not isinstance(command, Command):
        raise TypeError(f"Command {command} is not a Command")
    with _lock:
        if command in _commands_set:
            _commands_set.remove(command)
            _commands_map.pop(command.name)


def get_commands() -> list[Command]:
    with _lock:
        return list(_commands_set)


def run_command(name: str, args: FullArgs) -> None:
    with _lock:
        command = _commands_map.get(name)
    if command is None:
        raise RuntimeError(f'Could not find the "{name}" command.')
    command.main_func(args)
