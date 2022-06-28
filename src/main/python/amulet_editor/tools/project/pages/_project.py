import os
from os import R_OK
from pathlib import Path
from typing import Optional

from amulet_editor.tools.project._components import MCFunctionHighlighter, QCodeEditor
from PySide6.QtGui import QFontDatabase, QSyntaxHighlighter
from PySide6.QtWidgets import QVBoxLayout, QWidget

syntax_highlighters = {
    ".mcfunction": MCFunctionHighlighter,
}


class ProjectPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self.highlighter: Optional[QSyntaxHighlighter] = None

        self.setupUi()

    def show_file(self, file_path: str) -> None:
        if os.path.isfile(file_path) and os.access(file_path, R_OK):
            try:
                with open(file_path, "r") as text:
                    self.txe_file.setPlainText(text.read())

                # Remove current syntax highlighter
                if self.highlighter is not None:
                    self.highlighter.setDocument(None)

                # Attach new syntax highlighter to document
                highlighter = syntax_highlighters.get(Path(file_path).suffix, None)
                if highlighter is not None:
                    self.highlighter = highlighter()
                    self.highlighter.setDocument(self.txe_file.document())

            except UnicodeDecodeError:
                self.txe_file.clear()
                self.txe_file.setPlainText(f"Error Decoding File:\n{file_path}\n")

    def setupUi(self) -> None:
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        self.txe_file = QCodeEditor()
        self.txe_file.setFont(font)

        self.hlt_mcfunction = MCFunctionHighlighter()
        self.hlt_mcfunction.setDocument(self.txe_file.document())
        self.hlt_mcfunction.setDocument(None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.txe_file)

        self.setLayout(layout)
