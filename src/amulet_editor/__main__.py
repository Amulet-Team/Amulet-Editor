#!/usr/bin/env python3


def main():
    try:
        # Verify the python version
        import sys
        if sys.version_info[:2] < (3, 9):
            raise Exception("Must be using Python 3.9+")

        # This is required when running from a frozen bundle (eg pyinstaller)
        from multiprocessing import freeze_support
        freeze_support()

        # Initialise default paths
        from amulet_editor.data.paths._application import _init_paths
        _init_paths(None, None, None, None)

        from amulet_editor.application._console import init_console
        init_console()

        # Enable useful tracebacks for access violations and other hard crashes
        import faulthandler
        faulthandler.enable()

        from amulet_editor.application._main import app_main

    except Exception as e:
        try:
            import traceback
            import sys

        except ImportError as e:
            # Something has gone seriously wrong
            print(e)
            print("Failed to import requirements. Check that you extracted correctly.")
            input("Press ENTER to continue.")
        else:
            err = "\n".join(
                [traceback.format_exc()]
                + ["Failed to import requirements. Check that you extracted correctly."]
                * isinstance(e, ImportError)
                + [str(e)]
            )
            print(err)
            try:
                with open("crash.log", "w") as f:
                    f.write(err)
            except OSError:
                pass
            input("Press ENTER to continue.")
            sys.exit(1)

    else:
        # Everything imported correctly. Boot the app.
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
                from amulet_editor.models.widgets.traceback_dialog import (
                    display_exception_blocking,
                )

                if QApplication.instance() is None:
                    # QDialog needs an app otherwise it crashes
                    app = QApplication()
                display_exception_blocking(
                    title="Error Initialising Application",
                    error=str(e),
                    traceback="".join(traceback.format_exc()),
                )
            except:
                pass
            input("Press ENTER to continue...")
            raise e


if __name__ == "__main__":
    main()
