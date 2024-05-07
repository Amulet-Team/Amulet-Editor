from amulet.level.abc import Level

level: Level | None = None


def get_level() -> Level | None:
    return level
