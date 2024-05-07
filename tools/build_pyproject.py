"""
Qt Creator requires a JSON file to define all files that it can see.
This will probably get out of sync at some point so this program will generate it.
"""

import glob
import os
import json

ProjectRoot = os.path.dirname(os.path.dirname(__file__))


def main() -> None:
    paths = []
    for path in glob.glob(
        os.path.join(ProjectRoot, "src", "**", "*.ui"), recursive=True
    ):
        if os.path.isfile(path):
            paths.append(os.path.relpath(path, ProjectRoot))

    with open(
        os.path.join(os.path.dirname(__file__), "..", "Amulet-Editor.pyproject"), "w"
    ) as f:
        json.dump({"files": paths}, f, indent="\t")


if __name__ == "__main__":
    main()
