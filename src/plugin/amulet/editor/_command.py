from __future__ import annotations

from typing import NoReturn

from amulet.app.cli import register_command, Command


def _main(argv: list[str]) -> NoReturn:
    # Deferred import to avoid unnecessary imports
    from ._main import main

    main(argv)


register_command(
    Command(
        name="amulet_editor",
        main=_main,
    )
)
