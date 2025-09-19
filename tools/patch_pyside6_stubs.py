import os
import PySide6

PySide6Path = PySide6.__path__[0]

Patches: dict[str, list[tuple[str, str]]] = {
    os.path.join(PySide6Path, "QtCore.pyi"): [
        (
            # QByteArray
            "def data(self, /) -> bytes | bytearray | memoryview: ...",
            "def data(self) -> bytes: ...",
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
    ],
    os.path.join(PySide6Path, "QtWidgets.pyi"): [
        (
            # QLayoutItem
            "    def spacerItem(self, /) -> PySide6.QtWidgets.QSpacerItem: ...\n"
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget: ...",
            "    def spacerItem(self, /) -> PySide6.QtWidgets.QSpacerItem | None: ...\n"
            "    def widget(self, /) -> PySide6.QtWidgets.QWidget | None: ...",
        ),
        (
            # QStackedLayout
            "def itemAt(self, arg__1: int, /) -> PySide6.QtWidgets.QLayoutItem: ...",
            "def itemAt(self, index: int, /) -> PySide6.QtWidgets.QLayoutItem | None: ...",
        ),
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
