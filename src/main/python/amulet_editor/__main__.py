import sys


class PythonVersionError(Exception):
    def __init__(self, required_version: tuple) -> None:
        super().__init__(
            "Python {} required, found Python {}".format(
                ".".join([str(required_version[0]), str(required_version[1])]),
                ".".join([str(sys.version_info[0]), str(sys.version_info[1])]),
            )
        )


def main() -> None:
    try:
        if sys.version_info[:2] != (3, 9):
            raise PythonVersionError((3, 9))

        from amulet_editor.application.context._amulet_context import AMULET_CONTEXT

        AMULET_CONTEXT.run()
    finally:
        try:
            input("Press ENTER to continue...")
        except Exception:
            pass


if __name__ == "__main__":
    main()
