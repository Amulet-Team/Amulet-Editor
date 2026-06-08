from PySide6.QtCore import QCoreApplication, QSize, Qt, QEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class OpenWorldPageGUI(QWidget):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Widget
    ) -> None:
        super().__init__(parent, f)
        self.setProperty("backgroundColor", "background")

        self.verticalLayout = QVBoxLayout(self)

        self._lyt_header = QHBoxLayout()

        self.btn_back = QPushButton(self)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_back.sizePolicy().hasHeightForWidth())
        self.btn_back.setSizePolicy(sizePolicy)
        self.btn_back.setMinimumSize(QSize(30, 30))
        self.btn_back.setMaximumSize(QSize(30, 30))
        self._lyt_header.addWidget(self.btn_back)

        self._lbl_title = QLabel(self)
        self._lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lyt_header.addWidget(self._lbl_title)

        self._horizontal_spacer = QSpacerItem(
            30, 30, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        self._lyt_header.addItem(self._horizontal_spacer)
        self.verticalLayout.addLayout(self._lyt_header)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Shape.HLine)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.frame.setProperty("borderTop", "surface")
        self.verticalLayout.addWidget(self.frame)

        self.horizontalLayout = QHBoxLayout()

        self.load_file_button = QPushButton(self)
        self.horizontalLayout.addWidget(self.load_file_button)

        self.load_directory_button = QPushButton(self)
        self.horizontalLayout.addWidget(self.load_directory_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self._vertical_spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.verticalLayout.addItem(self._vertical_spacer)

        self._localise()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        self.setWindowTitle(
            QCoreApplication.translate(
                "plugin.amulet.editor.OpenWorldPage", "window_title", None
            )
        )
        self.btn_back.setText("")
        self._lbl_title.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.OpenWorldPage", "open_level", None
            )
        )
        self.load_file_button.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.OpenWorldPage", "open_file", None
            )
        )
        self.load_directory_button.setText(
            QCoreApplication.translate(
                "plugin.amulet.editor.OpenWorldPage", "open_directory", None
            )
        )
