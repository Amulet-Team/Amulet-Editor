#!/usr/bin/env python3

def _on_error(e):
    """Code to handle errors"""
    err_list = []
    try:
        import traceback

        err_list.append(traceback.format_exc())
    except:
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
except Exception as e:
    _on_error(e)


def main() -> None:
    try:
        from amulet_editor.application._app import AmuletEditor
    except Exception as e:
        _on_error(e)
        raise

    try:
        sys.exit(AmuletEditor().exec())
    except Exception as e:
        # TODO: Convert this to use logging
        print(f"Amulet Crashed. Sorry about that. Please report it to a developer if you think this is an issue. \n{traceback.format_exc()}")
        input("Press ENTER to continue...")
        raise e


if __name__ == "__main__":
    main()
