import os
import PySide6

PySide6Path = PySide6.__path__[0]

Patches: dict[str, list[tuple[str, str]]] = {
    os.path.join(PySide6Path, "QtCore.pyi"): [
        (
            # QTranslator
            "def translate(self, context: str, sourceText: str, /, disambiguation: str | None = ..., n: int = ...) -> str: ...",
            "def translate(self, context: str, sourceText: str, /, disambiguation: str | None = ..., n: int = ...) -> str | None: ...",
        ),
        (
            # QByteArray
            "def data(self, /) -> bytes | bytearray | memoryview: ...",
            "def data(self) -> bytes: ...",
        ),
        (
            # QObject and subclasses
            f"def parent(self, /) -> PySide6.QtCore.QObject: ...",
            f"def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtGui.pyi"): [
        (
            # QWindow
            "def setParent(self, parent: PySide6.QtGui.QWindow, /) -> None: ...",
            "def setParent(self, parent: PySide6.QtGui.QWindow | None, /) -> None: ...",
        ),
        (
            # QOpenGLFunctions
            "def glVertexAttribPointer(self, indx: int, size: int, type: int, normalized: int, stride: int, ptr: int, /) -> None: ...",
            "def glVertexAttribPointer(self, indx: int, size: int, type: int, normalized: int, stride: int, ptr: Shiboken.VoidPtr, /) -> None: ...",
        ),
        (
            # Subclasses of QObject
            f"def parent(self, /) -> PySide6.QtCore.QObject: ...",
            f"def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtWidgets.pyi"): [
        (
            # QButtonGroup
            "def checkedButton(self, /) -> PySide6.QtWidgets.QAbstractButton: ...",
            "def checkedButton(self, /) -> PySide6.QtWidgets.QAbstractButton | None: ...",
        ),
        (
            # QLayoutItem
            "    def spacerItem(self, /) -> PySide6.QtWidgets.QSpacerItem: ...\n"
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget: ...",
            "    def spacerItem(self, /) -> PySide6.QtWidgets.QSpacerItem | None: ...\n"
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget | None: ...",
        ),
        (
            # QScrollArea
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget: ...\n"
            "    def widgetResizable(self, /) -> bool: ...",
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget | None: ...\n"
            "    def widgetResizable(self, /) -> bool: ...",
        ),
        (
            # QSplitter
            "def replaceWidget(self, index: int, widget: PySide6.QtWidgets.QWidget, /) -> PySide6.QtWidgets.QWidget: ...",
            "def replaceWidget(self, index: int, widget: PySide6.QtWidgets.QWidget, /) -> PySide6.QtWidgets.QWidget | None: ...",
        ),
        (
            # QStackedLayout
            "def itemAt(self, arg__1: int, /) -> PySide6.QtWidgets.QLayoutItem: ...",
            "def itemAt(self, index: int, /) -> PySide6.QtWidgets.QLayoutItem | None: ...",
        ),
        (
            # QStackedLayout
            "    @typing.overload\n"
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget: ...\n"
            "    @typing.overload\n"
            "    def widget(self, arg__1: int, /) -> PySide6.QtWidgets.QWidget: ...\n",
            "    @typing.overload\n"
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget | None: ...\n"
            "    @typing.overload\n"
            "    def widget(self, arg__1: int, /) -> PySide6.QtWidgets.QWidget | None: ...\n",
        ),
        (
            # QStyleOption
            "    def initFrom(self, w: PySide6.QtWidgets.QWidget, /) -> None: ...\n\n\n",
            "    def initFrom(self, w: PySide6.QtWidgets.QWidget, /) -> None: ...\n"
            "    \n"
            "    direction: PySide6.QtCore.Qt.LayoutDirection\n"
            "    fontMetrics: PySide6.QtGui.QFontMetrics\n"
            "    palette: PySide6.QtGui.QPalette\n"
            "    rect: PySide6.QtCore.QRect\n"
            "    state: PySide6.QtWidgets.QStyle.StateFlag\n"
            "    styleObject: QObject\n"
            "    type: int\n"
            "    version: int\n\n\n",
        ),
        (
            # Subclasses of QObject
            f"def parent(self, /) -> PySide6.QtCore.QObject: ...",
            f"def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtHelp.pyi"): [
        (
            # Subclasses of QObject
            f"def parent(self, /) -> PySide6.QtCore.QObject: ...",
            f"def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        )
    ],
    os.path.join(PySide6Path, "QtPdf.pyi"): [
        (
            # Subclasses of QObject
            f"def parent(self, /) -> PySide6.QtCore.QObject: ...",
            f"def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        )
    ],
    os.path.join(PySide6Path, "QtRemoteObjects.pyi"): [
        (
            # Subclasses of QObject
            f"def parent(self, /) -> PySide6.QtCore.QObject: ...",
            f"def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        )
    ],
}


def main() -> None:
    for stub_path, patches in Patches.items():
        with open(stub_path) as f:
            stub = f.read()
        for find, replace in patches:
            stub = stub.replace(find, replace)
        with open(stub_path, "w") as f:
            f.write(stub)


if __name__ == "__main__":
    main()
