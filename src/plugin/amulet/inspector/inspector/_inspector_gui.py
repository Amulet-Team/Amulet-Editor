import os

from PySide6.QtCore import QCoreApplication, Qt, QEvent, QLocale
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from amulet.app.localisation import Translator, locale_changed

_translator: Translator | None = None


def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator()

        def _load_translations() -> None:
            _translator.load_lang(
                QLocale(),
                "",
                directory=os.path.join(os.path.dirname(__file__), "lang"),
            )

        _load_translations()
        QApplication.installTranslator(_translator)
        locale_changed.connect(_load_translations)
    return _translator


class InspectionToolGUI(QMainWindow):
    def __init__(
        self, parent: QWidget | None = None, flags: Qt.WindowType = Qt.WindowType.Window
    ) -> None:
        super().__init__(parent, flags)

        self._central_widget = QWidget(self)

        self._vertical_layout = QVBoxLayout(self._central_widget)

        self._horizontal_layout_2 = QHBoxLayout()

        self.inspect_button = QPushButton(self._central_widget)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.inspect_button.sizePolicy().hasHeightForWidth()
        )
        self.inspect_button.setSizePolicy(sizePolicy)
        self._horizontal_layout_2.addWidget(self.inspect_button)

        self.reload_button = QPushButton(self._central_widget)
        self._horizontal_layout_2.addWidget(self.reload_button)
        self._vertical_layout.addLayout(self._horizontal_layout_2)

        self.tree_widget = QTreeWidget(self._central_widget)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, "1")
        self.tree_widget.setHeaderItem(__qtreewidgetitem)
        self.tree_widget.header().setVisible(False)
        self._vertical_layout.addWidget(self.tree_widget)

        self._horizontal_layout_1 = QHBoxLayout()

        self.code_editor = QPlainTextEdit(self._central_widget)
        self._horizontal_layout_1.addWidget(self.code_editor)

        self.run_button = QPushButton(self._central_widget)
        sizePolicy1 = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding
        )
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.run_button.sizePolicy().hasHeightForWidth())
        self.run_button.setSizePolicy(sizePolicy1)
        self._horizontal_layout_1.addWidget(self.run_button)
        self._vertical_layout.addLayout(self._horizontal_layout_1)
        self.setCentralWidget(self._central_widget)

        self._localise()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate(
                "plugin.amulet.inspector.InspectionTool", "window_title", None
            )
        )
        self.inspect_button.setText("")
        self.reload_button.setText("")
        self.run_button.setText(
            QCoreApplication.translate(
                "plugin.amulet.inspector.InspectionTool", "run", None
            )
        )
