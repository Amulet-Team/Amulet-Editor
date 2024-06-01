import os
import PySide6

PySide6Path = PySide6.__path__[0]

Patches: dict[str, list[tuple[str, str]]] = {
    os.path.join(PySide6Path, "QtCore.pyi"): [
        (
            "def translate(self, context: Union[bytes, bytearray, memoryview], sourceText: Union[bytes, bytearray, memoryview], disambiguation: Union[bytes, bytearray, memoryview, NoneType] = ..., n: int = ...) -> str: ...",
            "def translate(self, context: str, sourceText: str, disambiguation: Union[str, NoneType] = ..., n: int = ...) -> Union[str, None]: ...",
        ),
        (
            "def data(self) -> Union[bytes, bytearray, memoryview]: ...",
            "def data(self) -> Union[bytes]: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtGui.pyi"): [
        (
            "def setParent(self, parent: PySide6.QtGui.QWindow",
            "def setParent(self, parent: Optional[PySide6.QtGui.QWindow]",
        ),
        (
            "def glVertexAttribPointer(self, indx: int, size: int, type: int, normalized: int, stride: int, ptr: int) -> None: ...",
            "def glVertexAttribPointer(self, indx: int, size: int, type: int, normalized: int, stride: int, ptr: Shiboken.VoidPtr) -> None: ...",
        ),
    ],
    os.path.join(PySide6Path, "QtWidgets.pyi"): [
        (
            "def spacerItem(self) -> PySide6.QtWidgets.QSpacerItem: ...\n    def widget(self) -> PySide6.QtWidgets.QWidget: ...",
            "def spacerItem(self) -> Optional[PySide6.QtWidgets.QSpacerItem]: ...\n    def widget(self) -> Optional[PySide6.QtWidgets.QWidget]: ...",
        ),
        (
            "def itemAt(self, arg__1: int) -> PySide6.QtWidgets.QLayoutItem: ...",
            "def itemAt(self, arg__1: int) -> Optional[PySide6.QtWidgets.QLayoutItem]: ...",
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
