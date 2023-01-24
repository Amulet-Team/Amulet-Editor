#!/usr/bin/env python3


def _on_error(e):
    """Code to handle errors"""
    err_list = []
    try:
        import traceback

        err_list.append(traceback.format_exc())
    except ImportError:
        pass
    if isinstance(e, ImportError):
        err_list.append(
            f"Failed to import requirements. Check that you extracted correctly."
        )
    err_list.append(str(e))
    err = "\n".join(err_list)
    print(err)
    # TODO: fix this path to a writable location
    with open("crash.log", "w") as f:
        f.write(err)
    input("Press ENTER to continue.")
    sys.exit(1)


try:
    import sys

    if sys.version_info[:2] < (3, 9):
        raise Exception("Must be using Python 3.9+")
    import traceback
except Exception as e_:
    _on_error(e_)


def main() -> None:
    try:
        from multiprocessing import freeze_support
    except Exception as e:
        _on_error(e)
        raise
    else:
        freeze_support()

    try:
        import logging
        import argparse
        from amulet_editor.application._app import main
        from amulet_editor.data.process._process import bootstrap, ProcessType

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--debug",
            help="Log debug information.",
            action="store_const",
            dest="loglevel",
            const=logging.DEBUG,
            default=logging.WARNING,
        )
        args, _ = parser.parse_known_args()

        logging.basicConfig(level=args.loglevel, format="%(levelname)s - %(message)s")
        logging.getLogger().setLevel(args.loglevel)
    except Exception as e:
        _on_error(e)
    else:
        try:
            bootstrap(ProcessType.Main, main)
        except Exception as e:
            logging.exception(e)
            logging.error(
                f"Amulet Crashed. Sorry about that. Please report it to a developer if you think this is an issue."
            )
            input("Press ENTER to continue...")
            raise e


if __name__ == "__main__":
    main()
