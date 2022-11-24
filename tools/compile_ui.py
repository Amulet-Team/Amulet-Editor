"""
Compile all Qt Designer UI files in the project to python files.
After generating it removes unused imports and reformats with Black.
"""

import glob
import os
import subprocess
import sys

ProjectRoot = os.path.dirname(os.path.dirname(__file__))
UIC = os.path.join(os.path.dirname(__file__), "uic.exe")


def main():
    for ui_path in glob.glob(os.path.join(ProjectRoot, "src", "**", "*.ui"), recursive=True):
        py_path = ui_path[:-2] + "py"
        if os.path.exists(py_path):
            with open(py_path) as f:
                if "Created by: Qt User Interface Compiler" not in f.read():
                    print(f"Skipping compilation of {ui_path} because a user generated python file would be overwritten.")
                    continue
        subprocess.run([UIC, ui_path, "-o", py_path])
        subprocess.run(["autoflake", "--in-place", "--remove-unused-variables", "--imports=PySide6", py_path])
        subprocess.run([sys.executable, "-m", "black", py_path])


if __name__ == '__main__':
    main()
