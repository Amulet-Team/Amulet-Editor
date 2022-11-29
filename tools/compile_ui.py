"""
Compile all Qt Designer UI files in the project to python files.
After generating it removes unused imports and reformats with Black.
"""

import glob
import os
import subprocess
import sys
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

ProjectRoot = os.path.dirname(os.path.dirname(__file__))
UIC = os.path.join(os.path.dirname(__file__), "uic.exe")


def _compile_ui_file(ui_path: str):
    py_path = ui_path[:-2] + "py"

    # Make sure we are not overwriting user code
    if os.path.exists(py_path):
        with open(py_path) as f:
            if "Created by: Qt User Interface Compiler" not in f.read():
                print(f"Skipping compilation of {ui_path} because a user generated python file would be overwritten.")
                return

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
    py = re.sub(f"def setupUi\\(self, {class_name}\\):", "def __init__(self, *args, **kwargs):\n        super().__init__(*args, **kwargs)", py)
    # Replace retranslateUi with localise
    py = re.sub(f"def retranslateUi\\(self, {class_name}\\):", "def localise(self):", py)
    py = py.replace(f"self.retranslateUi({class_name})", "self.localise()")
    # Replace class name with self
    py = re.sub(f"(?<!\")\\b{class_name}\\b(?!\")", "self", py)
    # Add in line breaks before assignments
    py = re.sub(f"\r?\n(?=\s*self\..*? = )", "\n\n", py)
    py = re.sub(f"\r?\n(?=\s*self\.localise\(\))", "\n\n", py)

    # Write the file back
    with open(py_path, "w") as pyf:
        pyf.write(py)

    # Remove unused variables
    subprocess.run(["autoflake", "--in-place", "--remove-unused-variables", "--imports=PySide6", py_path])
    # Reformat
    subprocess.run([sys.executable, "-m", "black", py_path])


def main():
    # For each UI file in the project
    with ThreadPoolExecutor() as executor:
        for ui_path in glob.glob(os.path.join(ProjectRoot, "src", "**", "*.ui"), recursive=True):
            executor.submit(_compile_ui_file, ui_path)


if __name__ == '__main__':
    main()
