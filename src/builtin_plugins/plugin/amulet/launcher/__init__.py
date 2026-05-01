from typing import NoReturn

from amulet.app.cli import register_command, Command


def launcher_command(args: list[str]) -> NoReturn:
    pass


_launcher_command = Command(name="amulet_launcher", main=launcher_command)

register_command(_launcher_command)
