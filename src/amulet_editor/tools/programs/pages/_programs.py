from typing import Optional

from amulet_editor.tools.project._components import MCFunctionHighlighter, QCodeEditor
from PySide6.QtGui import QFontDatabase, QSyntaxHighlighter
from PySide6.QtWidgets import QVBoxLayout, QWidget


class ProgramsPage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)

        self.highlighter: Optional[QSyntaxHighlighter] = None

        self.setupUi()

    def setupUi(self):
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)

        self.txe_file = QCodeEditor()
        self.txe_file.setFont(font)

        self.hlt_mcfunction = MCFunctionHighlighter()
        self.hlt_mcfunction.setDocument(self.txe_file.document())
        self.hlt_mcfunction.setDocument(None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.txe_file)

        self.setLayout(layout)
