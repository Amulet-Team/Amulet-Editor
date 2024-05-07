"""
Compile all Qt Designer UI files in the project to python files.
After generating it removes unused imports and reformats with Black.
"""

import glob
import os
import subprocess
import sys
import re
import traceback
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import PySide6

ProjectRoot = os.path.dirname(os.path.dirname(__file__))
UIC = os.path.join(PySide6.__path__[0], "uic.exe")


def _compile_ui_file(ui_path: str) -> str | None:
    py_path = ui_path[:-2] + "py"

    # Make sure we are not overwriting user code
    if os.path.exists(py_path):
        with open(py_path) as f:
            if "Created by: Qt User Interface Compiler" not in f.read():
                print(
                    f"Skipping compilation of {ui_path} because a user generated python file would be overwritten."
                )
                return None

    # Convert the UI file to python code
    subprocess.run(["pyside6-uic", ui_path, "-o", py_path])

    # Read the file
    with open(py_path) as pyf:
        py = pyf.read()

    ui = ET.parse(ui_path)
    class_name = ui.find("class").text
    super_name = ui.find("widget").attrib["class"]

    # Run some postprocessing
    # Remove comments. The ones generated do not add anything
    py = re.sub(r"\r?\n\s*#(?!#).*", "\n", py)
    # Remove all duplicate line breaks
    py = re.sub(r"\r?\n\s*\r?\n", "\n", py)
    # Add super class
    py = py.replace("(object)", f"({super_name})")
    # Replace setupUi with constructor
    py = re.sub(
        f"def setupUi\\(self, {class_name}\\):",
        "def __init__(self, *args, **kwargs) -> None:\n        super().__init__(*args, **kwargs)",
        py,
    )

    py = py.replace(f"self.retranslateUi({class_name})", "self._localise()")
    # Replace class name with self
    py = re.sub(f'(?<!")\\b{class_name}\\b(?!")', "self", py)
    # Add in line breaks before assignments
    py = re.sub(r"\r?\n(?=\s*self\..*? = )", "\n\n", py)
    py = re.sub(r"\r?\n(?=\s*self\._localise\(\))", "\n\n", py)
    # Replace retranslateUi with _localise
    py = py.replace(
        "def retranslateUi(self, self):",
        "def changeEvent(self, event: QEvent) -> None:\n        super().changeEvent(event)\n        if event.type() == QEvent.Type.LanguageChange:\n            self._localise()\n    def _localise(self) -> None:",
    )
    py = re.sub(
        r"from PySide6\.QtCore import \(.*?\)",
        lambda match: match.group(0)[:-1] + ", QEvent)",
        py,
        flags=re.DOTALL,
    )

    # Write the file back
    with open(py_path, "w") as pyf:
        pyf.write(py)

    # Remove unused variables
    subprocess.run(
        [
            "autoflake",
            "--in-place",
            "--remove-unused-variables",
            "--imports=PySide6",
            py_path,
        ]
    )

    return py_path


def _try_compile_ui_file(ui_path: str) -> str | None:
    try:
        return _compile_ui_file(ui_path)
    except Exception:
        print(traceback.format_exc())


def main() -> None:
    futures = []
    # For each UI file in the project
    with ThreadPoolExecutor() as executor:
        for ui_path in glob.glob(
            os.path.join(ProjectRoot, "src", "**", "*.ui"), recursive=True
        ):
            futures.append(executor.submit(_try_compile_ui_file, ui_path))

    paths = [f.result() for f in futures]
    if paths:
        subprocess.run([sys.executable, "-m", "black", *paths])


if __name__ == "__main__":
    main()
