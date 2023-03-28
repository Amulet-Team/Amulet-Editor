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
except Exception as e_:
    _on_error(e_)


def main() -> None:
    try:
        from multiprocessing import freeze_support
        freeze_support()
        import logging

        from amulet_editor.application._app import app_main
        from amulet_editor.models.widgets import AmuletTracebackDialog

        # Initialise logging at the highest level until configured otherwise.
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s - %(message)s")
        logging.getLogger().setLevel(logging.WARNING)

    except Exception as e:
        _on_error(e)
    else:
        try:
            app_main()
        except Exception as e:
            logging.exception(e)
            logging.error(
                f"Amulet Crashed. Sorry about that. Please report it to a developer if you think this is an issue."
            )
            try:
                import traceback
                from PySide6.QtWidgets import QApplication
                if QApplication.instance() is None:
                    # QDialog needs an app otherwise it crashes
                    app = QApplication()
                dialog = AmuletTracebackDialog(
                    title="Error Initialising Application",
                    error=str(e),
                    traceback="".join(traceback.format_exc()),
                )
                dialog.exec()
            except:
                pass
            input("Press ENTER to continue...")
            raise e


if __name__ == "__main__":
    main()
