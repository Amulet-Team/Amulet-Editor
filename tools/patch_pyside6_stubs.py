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
            "def parent(self, /) -> PySide6.QtCore.QObject: ...",
            "def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtGui.pyi"): [
        (
            # QOpenGLFunctions
            "def glVertexAttribPointer(self, indx: int, size: int, type: int, normalized: int, stride: int, ptr: int, /) -> None: ...",
            "def glVertexAttribPointer(self, indx: int, size: int, type: int, normalized: int, stride: int, ptr: Shiboken.VoidPtr, /) -> None: ...",
        ),
        (
            # Subclasses of QObject
            "def parent(self, /) -> PySide6.QtCore.QObject: ...",
            "def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtWidgets.pyi"): [
        (
            # QSplitter
            "def replaceWidget(self, index: int, widget: PySide6.QtWidgets.QWidget, /) -> PySide6.QtWidgets.QWidget: ...",
            "def replaceWidget(self, index: int, widget: PySide6.QtWidgets.QWidget, /) -> PySide6.QtWidgets.QWidget | None: ...",
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
            "def parent(self, /) -> PySide6.QtCore.QObject: ...",
            "def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtHelp.pyi"): [
        (
            # Subclasses of QObject
            "def parent(self, /) -> PySide6.QtCore.QObject: ...",
            "def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        )
    ],
    os.path.join(PySide6Path, "QtPdf.pyi"): [
        (
            # Subclasses of QObject
            "def parent(self, /) -> PySide6.QtCore.QObject: ...",
            "def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
        )
    ],
    os.path.join(PySide6Path, "QtRemoteObjects.pyi"): [
        (
            # Subclasses of QObject
            "def parent(self, /) -> PySide6.QtCore.QObject: ...",
            "def parent(self, /) -> PySide6.QtCore.QObject | None: ...",
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
