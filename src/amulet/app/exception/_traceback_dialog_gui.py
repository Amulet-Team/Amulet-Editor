from PySide6.QtCore import QCoreApplication, QMetaObject, QSize, Qt, QEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TracebackDialogGUI(QDialog):
    def __init__(
        self, parent: QWidget | None = None, f: Qt.WindowType = Qt.WindowType.Dialog
    ) -> None:
        super().__init__(parent, f)
        if not self.objectName():
            self.setObjectName("TracebackDialog")
        self.resize(400, 300)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setObjectName("_main_layout")

        self._header_layout = QHBoxLayout()
        self._header_layout.setObjectName("_header_layout")

        self._alert_image = QLabel(self)
        self._alert_image.setObjectName("_alert_image")
        self._alert_image.setMinimumSize(QSize(32, 32))
        self._alert_image.setMaximumSize(QSize(32, 32))
        self._header_layout.addWidget(self._alert_image)

        self._error_text = QLabel(self)
        self._error_text.setObjectName("_error_text")
        self._header_layout.addWidget(self._error_text)
        self._header_layout.setStretch(1, 1)
        self._main_layout.addLayout(self._header_layout)

        self._traceback_text = QTextEdit(self)
        self._traceback_text.setObjectName("_traceback_text")
        self._traceback_text.setReadOnly(True)
        self._main_layout.addWidget(self._traceback_text)

        self._button_layout = QHBoxLayout()
        self._button_layout.setObjectName("_button_layout")

        self._spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._button_layout.addItem(self._spacer)

        self._copy_button = QPushButton(self)
        self._copy_button.setObjectName("_copy_button")
        self._button_layout.addWidget(self._copy_button)

        self._ok_button_box = QDialogButtonBox(self)
        self._ok_button_box.setObjectName("_ok_button_box")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self._ok_button_box.sizePolicy().hasHeightForWidth()
        )
        self._ok_button_box.setSizePolicy(sizePolicy)
        self._ok_button_box.setOrientation(Qt.Orientation.Horizontal)
        self._ok_button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok)
        self._button_layout.addWidget(self._ok_button_box)
        self._main_layout.addLayout(self._button_layout)

        self._localise()
        self._ok_button_box.rejected.connect(self.reject)
        self._ok_button_box.accepted.connect(self.accept)
        QMetaObject.connectSlotsByName(self)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._localise()

    def _localise(self) -> None:
        title = QCoreApplication.translate(
            "amulet.app.TracebackDialog", "window_title", None
        )
        if title == "window_title":
            title = "Exception Traceback"
        self.setWindowTitle(title)
        self._alert_image.setText("")
        self._error_text.setText("")
        copy_button_text = QCoreApplication.translate(
            "amulet.app.TracebackDialog", "copy_error", None
        )
        if copy_button_text == "copy_error":
            copy_button_text = "Copy Error"
        self._copy_button.setText(copy_button_text)
