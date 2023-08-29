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

        # Import and boot the app.
        from amulet_editor.application._main import app_main

        app_main()

    except Exception as e:
        # Something crashed

        # Log the output to a file
        try:
            # If the logging module has been initialised then log to that
            import logging
            import sys
            import os
            from datetime import datetime

            if not any(
                isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers
            ):
                # Set up a file handler if one does not exist

                try:
                    from amulet_editor.data.paths._application import logging_directory

                    log_dir = logging_directory()
                except Exception:
                    log_dir = "."

                file_path = os.path.join(
                    log_dir,
                    f"amulet-log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{os.getpid()}.txt",
                )
                file_handler = logging.FileHandler(file_path)

                logging.basicConfig(
                    level=logging.WARNING,
                    format="%(levelname)s - %(threadName)s - %(name)s - %(message)s",
                    force=True,
                    handlers=[logging.StreamHandler(sys.__stderr__), file_handler],
                )

            logging.exception(e)
            logging.error(
                "Amulet Crashed. Sorry about that. Please report it to a developer if you think this is an issue."
            )

        except Exception:
            # If using the logging module failed then try just writing it.
            try:
                import traceback

                tb = traceback.format_exc()
            except Exception:
                tb = None

            try:
                print(e)
                if tb is not None:
                    print(tb)
                print(
                    "Amulet Crashed. Sorry about that. Please report it to a developer if you think this is an issue."
                )
                import os

                try:
                    from amulet_editor.data.paths._application import logging_directory

                    log_dir = logging_directory()
                except Exception:
                    log_dir = "."
                with open(os.path.join(log_dir, f"crash_{os.getpid()}.log"), "w") as f:
                    if tb is not None:
                        f.write(tb)
                    f.write(str(e))
                    f.write(
                        "Amulet Crashed. Sorry about that. Please report it to a developer if you think this is an issue."
                    )
            except Exception:
                pass

        try:
            # Try reporting the crash with a GUI
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
        except Exception:
            pass

        try:
            # If a console is being shown then pause to let the user read it.
            import sys

            if sys.stdin is not None:
                input("Press ENTER to continue.")
        except Exception:
            pass

        raise e


if __name__ == "__main__":
    main()
