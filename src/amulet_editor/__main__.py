#!/usr/bin/env python3

def _on_error(e):
    """Code to handle errors"""
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


try:
    from multiprocessing import freeze_support

    freeze_support()
    import sys
    import logging
    import faulthandler

    faulthandler.enable()

    if sys.version_info[:2] < (3, 9):
        raise Exception("Must be using Python 3.9+")
except Exception as e_:
    _on_error(e_)


def main():
    try:
        # Initialise logging at the highest level until configured otherwise.
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s - %(message)s")
        logging.getLogger().setLevel(logging.WARNING)

        from amulet_editor.application._main import app_main
        from amulet_editor.models.widgets.traceback_dialog import display_exception_blocking

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
