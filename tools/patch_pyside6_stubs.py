import os
import PySide6

PySide6Path = PySide6.__path__[0]

Patches: dict[str, list[tuple[str, str]]] = {
    os.path.join(PySide6Path, "QtCore.pyi"): [
        (
            "def translate(self, context: Union[bytes, bytearray, memoryview], sourceText: Union[bytes, bytearray, memoryview], disambiguation: Union[bytes, bytearray, memoryview, NoneType] = ..., n: int = ...) -> str: ...",
            "def translate(self, context: Union[str], sourceText: Union[str], disambiguation: Union[str, NoneType] = ..., n: int = ...) -> str: ...",
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
    ]
}


def main() -> None:
    for stub_path, patches in Patches.items():
        with open(stub_path) as f:
            stub = f.read()
        for find, replace in patches:
            stub = stub.replace(find, replace)
        with open(stub_path, "w") as f:
            f.write(stub)


if __name__ == '__main__':
    main()
