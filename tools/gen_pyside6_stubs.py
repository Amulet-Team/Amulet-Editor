"""
There are some issues with the stub files distributed with PySide6 which make development difficult.
This script will modify the stub files to fix some of those issues.
"""

from __future__ import annotations

import typing
from typing import Optional, Union, overload
import inspect
import os
from enum import EnumType, Enum, IntEnum
import pkgutil
import importlib
from types import ModuleType
from io import StringIO
import copy
import sys
import shutil
import subprocess

import PySide6
from PySide6.QtCore import Signal, Slot
from PySide6.support.signature.mapping import ArrayLikeVariable, Default, Instance, Invalid

StubPath = "stubs"


BuiltInClassAttrs = {
    "__abstractmethods__",
    "__doc__",
    "__init_subclass__",
    "__module__",
    "__name__",
    "__qualname__",
    "__subclasshook__",
    "__mro__",
    "__base__",
    "__bases__",
    "__annotations__",
    "__abstractmethods__",
    "__base__",
    "__basicsize__",
    "__dictoffset__",
    "__flags__",
    "__itemsize__",
    "__weakrefoffset__",
    "__instancecheck__",
    "__class__",
    "__delattr__",
    "__dict__",
    "__dir__",
    "__init_subclass__",
    "__new__",
    "__subclasshook__",
    "__abstractmethods__",
    "__annotations__",
    "__text_signature__",
    "__signature__",
    "__prepare__",
    "__members__",
    "__isabstractmethod__",
    "__setattr__",
    "__opaque_container__",
    "__copy__"
}


Patches: dict[str, tuple[tuple[str, str], ...]] = {
    "QtWidgets.pyi": (
        ("def setParent(self, parent: PySide6.QtWidgets.QWidget", "def setParent(self, parent: Optional[PySide6.QtWidgets.QWidget]"),
    ),
    "QtCore.pyi": (
        ("def setParent(self, parent: PySide6.QtCore.QObject", "def setParent(self, parent: Optional[PySide6.QtCore.QObject]"),
    ),
    "QtGui.pyi": (
        ("def setParent(self, parent: PySide6.QtGui.QWindow", "def setParent(self, parent: Optional[PySide6.QtGui.QWindow]"),
    )
}

Indent = "    "

# ModuleAlias = {}
# for __sub_module in pkgutil.iter_modules(PySide6.__path__, f"{PySide6.__name__}."):
#     ModuleAlias[__sub_module.name[len(PySide6.__name__) + 1:]] = __sub_module.name
# ModuleAlias["Shiboken"] = "shiboken6"
# ModuleAlias["shibokensupport"] = "PySide6.support"


class ImportManager:
    def __init__(self):
        self._attrs: dict[str, set[tuple[str, str]]] = {}
        # self._hidden_attrs: dict[str, set[tuple[str, str]]] = {}
        self._mods: dict[str, set[str]] = {}

    def import_attr(self, mod_name: str, attr: str, alias: str = None):
        if alias is None:
            alias = attr
        if not (isinstance(mod_name, str) and isinstance(attr, str) and isinstance(alias, str)):
            raise ValueError
        self._attrs.setdefault(mod_name, set()).add((attr, alias))

    # def hidden_import_attr(self, mod_name: str, attr: str, alias: str = ""):
    #     if not (isinstance(mod_name, str) and isinstance(attr, str) and isinstance(alias, str)):
    #         raise ValueError
    #     self._hidden_attrs.setdefault(mod_name, set()).add((attr, alias))

    def import_module(self, mod_name: str, alias: str = None):
        if alias is None:
            alias = mod_name
        if not (isinstance(mod_name, str) and isinstance(alias, str)):
            raise ValueError
        self._mods.setdefault(mod_name, set()).add(alias)

    def pack(self) -> str:
        pack = []
        for mod_name, data in sorted(self._attrs.items()):
            if mod_name == "builtins":
                continue
            pack.append(f"from {mod_name} import ")
            first = True
            for attr, alias in data:
                if not first:
                    pack.append(", ")
                first = False
                if attr != alias:
                    pack.append(f"{attr} as {alias}")
                else:
                    pack.append(f"{attr}")

            pack.append("\n")

        for mod_name, aliases in sorted(self._mods.items()):
            if mod_name == "builtins":
                continue
            for alias in aliases:
                if mod_name != alias:
                    pack.append(f"import {mod_name} as {alias}\n")
                else:
                    pack.append(f"import {mod_name}\n")

        pack.append("\n")

        return "".join(pack)


@overload
def get_module_qualname(obj: ModuleType) -> tuple[str, Optional[str]]:
    ...

@overload
def get_module_qualname(obj) -> tuple[str, str]:
    ...

def get_module_qualname(obj):
    """Get the module the object was defined in and the qualified name within that module."""
    # Get the qualified name from the object
    qualname = getattr(obj, "__qualname__", None) or obj.__class__.__qualname__

    # Find the module name
    module_name = None
    if inspect.ismethoddescriptor(obj):
        module_name = obj.__objclass__.__module__
    elif inspect.ismodule(obj):
        module_name = obj.__name__

    if module_name is None:
        module_name = getattr(obj, "__module__", None)

    if module_name is None:
        module_name = obj.__class__.__module__

    if module_name is None:
        raise RuntimeError

    # Some PySide and Shiboken module names are a bit jank. Fix them.
    if module_name.startswith("shibokensupport"):
        module_name = f"PySide6.support{module_name[15:]}"
    elif module_name.startswith("Shiboken"):
        module_name = f"shiboken6{module_name[8:]}"
    elif module_name in {
        "Qt3DAnimation",
        "Qt3DCore",
        "Qt3DExtras",
        "Qt3DInput",
        "Qt3DLogic",
        "Qt3DRender",
        "QtAxContainer",
        "QtBluetooth",
        "QtCharts",
        "QtConcurrent",
        "QtCore",
        "QtDataVisualization",
        "QtDesigner",
        "QtGui",
        "QtHelp",
        "QtMultimedia",
        "QtMultimediaWidgets",
        "QtNetwork",
        "QtNetworkAuth",
        "QtNfc",
        "QtOpenGL",
        "QtOpenGLWidgets",
        "QtPdf",
        "QtPdfWidgets",
        "QtPositioning",
        "QtPrintSupport",
        "QtQml",
        "QtQuick",
        "QtQuick3D",
        "QtQuickControls2",
        "QtQuickWidgets",
        "QtRemoteObjects",
        "QtScxml",
        "QtSensors",
        "QtSerialPort",
        "QtSpatialAudio",
        "QtSql",
        "QtStateMachine",
        "QtSvg",
        "QtSvgWidgets",
        "QtTest",
        "QtUiTools",
        "QtWebChannel",
        "QtWebEngineCore",
        "QtWebEngineQuick",
        "QtWebEngineWidgets",
        "QtWebSockets",
        "QtWidgets",
        "QtXml",
    }:
        module_name = f"PySide6.{module_name}"

    if module_name == "PySide6.support.signature.loader":
        # This isn't directly importable for some reason
        module_name = "PySide6.support.signature"
        qualname = f"loader.{qualname}"

    return module_name, qualname


def get_module_name(obj) -> str:
    """Get the module name where this object was defined."""
    return get_module_qualname(obj)[0]


def get_qualname(obj) -> str:
    return get_module_qualname(obj)[1]


def get_name(obj) -> str:
    return getattr(obj, "__name__", None) or obj.__class__.__name__


def get_path(obj) -> tuple[Optional[str], str, str]:
    mod, qual = get_module_qualname(obj)
    return mod, qual, get_name(obj)


def get_module(obj) -> ModuleType:
    return importlib.import_module(get_module_name(obj))


# def add_import(obj, module_alias: dict[str, str]):
#     mod = inspect.getmodule(obj)
#     if mod is None:
#         mod_str = obj.__module__
#         if mod_str in module_alias:
#             mod_str = module_alias[mod_str]
#             mod = importlib.import_module(mod_str)
#     if mod is None:
#         raise RuntimeError
#     return mod


class State:
    def __init__(self, module: ModuleType, imports: ImportManager, contents: StringIO, indentation: int):
        self.module = module
        self.imports = imports
        self.contents = contents
        self.indentation = indentation

    def __enter__(self):
        self.indentation += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indentation -= 1


def generate_class(cls: type, state: State):
    superclasses = []
    for superclass in cls.__bases__:
        if superclass is object or superclass is type:
            continue
        mod_name, qualname, name = get_path(superclass)
        if mod_name == "builtins":
            superclasses.append(qualname)
        else:
            superclasses.append(f"{mod_name}.{qualname}")
        state.imports.import_module(mod_name)

    sup = f"({', '.join(superclasses)})" if superclasses else ""
    state.contents.write(f"{Indent * state.indentation}class {cls.__name__}{sup}:\n")
    start = state.contents.tell()

    with state:
        for attr_name in dir(cls):
            if attr_name in BuiltInClassAttrs:
                continue
            elif attr_name in {"from"}:
                # Uncallable from python
                state.contents.write(f"{Indent * state.indentation}# {attr_name} = Any  # 2\n")
                continue

            attr = getattr(cls, attr_name)
            if inspect.isclass(attr):
                defmod = get_module(attr)
                defmod_name = get_module_name(attr)

                if defmod is state.module and f"{cls.__qualname__}.{attr_name}" == attr.__qualname__:
                    # This is the definition
                    generate_class(attr, state)
                elif next((getattr(base, attr_name) for base in cls.__bases__ if hasattr(base, attr_name)), None) is attr:
                    # Defined in the base
                    pass
                elif defmod is not None:
                    state.imports.import_module(defmod_name)
                    state.contents.write(f"{Indent * state.indentation}{attr_name} = {defmod_name}.{attr.__qualname__}\n")
                else:
                    mod_name, qualname = get_module_qualname(cls)
                    print(f"could not find module for {mod_name}.{qualname}.{attr_name}")

            elif isinstance(attr, Signal):
                state.imports.import_attr("PySide6.QtCore", "SignalInstance")
                # state.contents.write(f"{Indent * state.indentation}{attr_name} = {attr}\n")
                state.contents.write(f"{Indent * state.indentation}{attr_name}: SignalInstance  # {attr}\n")

            elif inspect.ismethod(attr) or inspect.ismethoddescriptor(attr):
                mod_name, qualname = get_module_qualname(attr)

                if mod_name == get_module_name(state.module) and qualname == f"{cls.__qualname__}.{attr_name}":
                    # This is the definition
                    generate_callable(attr, state)
                elif next((get_module_qualname(getattr(base, attr_name)) for base in cls.__bases__ if hasattr(base, attr_name)), None) == (mod_name, qualname):
                    # Defined in the base
                    pass
                elif mod_name is not None:
                    state.imports.import_module(mod_name)
                    state.contents.write(f"{Indent * state.indentation}{attr_name} = {mod_name}.{attr.__qualname__}\n")
                else:
                    state.imports.import_attr("typing", "Any")
                    state.contents.write(f"{Indent * state.indentation}{attr_name} = Any  # 1\n")
                    print(f"could not find module for {get_module_name(cls)}.{cls.__qualname__}.{attr_name}")

                # defmod = get_module(attr)
                # defmod_name = get_module_name(attr)
                #
                # if defmod is state.module and f"{cls.__qualname__}.{attr_name}" == attr.__qualname__:
                #     # This is the definition
                #     generate_callable(attr, state)
                # elif getattr(next((getattr(base, attr_name) for base in cls.__bases__ if hasattr(base, attr_name)), None), "__func__") is attr.__func__:
                #     # Defined in the base
                #     pass
                # elif defmod is not None:
                #     state.imports.import_module(defmod_name)
                #     state.contents.write(f"{Indent * state.indentation}{attr_name} = {defmod_name}.{attr.__qualname__}\n")
                # else:
                #     print(f"could not find module for {get_module_name(cls)}.{cls.__qualname__}.{attr_name}")

            # elif inspect.ismethoddescriptor(attr):
            #     defmod = get_module(attr)
            #     defmod_name = get_module_name(attr)
            #
            #     if defmod is state.module and f"{cls.__qualname__}.{attr_name}" == attr.__qualname__:
            #         # This is the definition
            #         generate_callable(attr, state)
            #     elif getattr(next((getattr(base, attr_name) for base in cls.__bases__ if hasattr(base, attr_name)), None), "__func__") is attr.__func__:
            #         # Defined in the base
            #         pass
            #     elif defmod is not None:
            #         state.imports.import_module(defmod_name)
            #         state.contents.write(f"{Indent * state.indentation}{attr_name} = {defmod_name}.{attr.__qualname__}\n")
            #     else:
            #         print(f"could not find module for {get_module_name(cls)}.{cls.__qualname__}.{attr_name}")

            else:
                state.imports.import_attr("typing", "Any")
                state.contents.write(f"{Indent * state.indentation}{attr_name} = Any  # 2\n")
                print(f"unhandled class variable {cls.__qualname__}.{attr_name} {attr}")

    if start == state.contents.tell():
        state.contents.write(f"{Indent * state.indentation}\tpass\n")
    state.contents.write("\n\n")


def streamline_args(obj, state: State, replace: dict[str, str]):
    if isinstance(obj, (list, tuple)):
        for arg in obj:
            streamline_args(typing.get_args(arg), state, replace)
    else:
        streamline_type(obj, state, replace)


def streamline_type(obj, state: State, replace: dict[str, str]):
    if obj is None or obj is inspect.Signature.empty:
        return
    # elif isinstance(obj, (Default, Instance, Invalid)):
    #     replace[repr(obj)] = "..."
    #     return
    mod_name, qualname, name = get_path(obj)
    if mod_name == "builtins":
        return
    elif mod_name.startswith("shibokensupport"):
        replace["shibokensupport"] = "PySide6.support"

    if mod_name in {"typing"}:
        state.imports.import_attr(mod_name, name)
    else:
        state.imports.import_module(mod_name)

    streamline_args(typing.get_args(obj), state, replace)


def stringify_signature(signature: inspect.Signature, state: State) -> str:
    replace = {}

    params = dict(signature.parameters)
    for param_name in list(params):
        param = params[param_name]
        streamline_type(param.annotation, state, replace)
        default = param.default
        if isinstance(default, (Default, Instance, Invalid)) or default is int or (inspect.isclass(default) and issubclass(default, (Enum, EnumType))) or default is PySide6.support.signature.mapping.ellipsis:
            params[param_name] = param.replace(default=Ellipsis)
        elif isinstance(default, (Enum,)):
            params[param_name] = param.replace(default=default.value)
        elif default is param.empty or default is None or isinstance(default, (int, str, float, dict, list, PySide6.QtCore.QCborTag, PySide6.QtCore.QRect)):
            streamline_type(param.default, state, replace)
        else:
            streamline_type(param.default, state, replace)

    signature = inspect.Signature(parameters=list(params.values()), return_annotation=signature.return_annotation)

    streamline_type(signature.return_annotation, state, replace)

    signature_str = str(signature)

    for short, full in replace.items():
        signature_str = signature_str.replace(full, short)

    if signature_str.endswith(" -> None"):
        signature_str = signature_str[:-8]

    return signature_str


def generate_callable(func, state: State):
    indent = "    " * state.indentation
    try:
        signature = getattr(func, "__signature__", None) or inspect.signature(func)
    except ValueError:
        if inspect.ismethod(func) or inspect.ismethoddescriptor(func) or inspect.ismethodwrapper(func):
            state.contents.write(f"{indent}def {func.__name__}(self, *args, **kwargs):...\n")
        else:
            state.contents.write(f"{indent}def {func.__name__}(*args, **kwargs):...\n")
    else:
        if isinstance(signature, inspect.Signature):
            state.contents.write(f"{indent}def {func.__name__}{stringify_signature(signature, state)}:...\n")
        elif isinstance(signature, list):
            for sig in signature:
                state.contents.write(f"{indent}@overload\n{indent}def {func.__name__}{stringify_signature(sig, state)}:...\n")
            state.imports.import_attr("typing", "overload", "overload")
        else:
            raise TypeError


def generate_module(mod: ModuleType, state: State):
    mod_name = get_module_name(mod)

    for attr_name in dir(mod):
        if attr_name.startswith("_"):
            continue

        attr = getattr(mod, attr_name)

        if inspect.isclass(attr):
            defmod_name = get_module_name(attr)
            defmod = get_module(attr)
            if defmod is mod:
                if attr_name == attr.__qualname__:
                    # This is the definition
                    generate_class(attr, state)
                else:
                    # Alias from the same module
                    state.contents.write(f"{attr_name} = {attr.__qualname__}")
            elif defmod is not None:
                state.imports.import_attr(defmod_name, attr.__name__, attr_name)
            else:
                state.imports.import_attr("typing", "Any")
                state.contents.write(f"{attr_name} = Any  # 3\n")
                print(f"could not find module for {mod_name}.{attr_name}")
        elif callable(attr):
            defmod_name = get_module_name(attr)
            defmod = get_module(attr)
            if defmod is mod:
                if attr_name == attr.__qualname__:
                    # This is the definition
                    generate_callable(attr, state)
                else:
                    # Alias from the same module
                    state.contents.write(f"{attr_name} = {mod_name}.{attr.__qualname__}")
            elif defmod is not None:
                state.imports.import_attr(defmod_name, attr.__name__, attr_name)
            else:
                state.imports.import_attr("typing", "Any")
                state.contents.write(f"{attr_name} = Any  # 4\n")
                print(f"could not find module for {mod_name}.{attr_name}")
        elif inspect.ismodule(attr):
            state.imports.import_module(attr.__name__, attr_name)
        else:
            state.imports.import_attr("typing", "Any")
            state.contents.write(f"{attr_name} = Any  # 5\n")
            print(f"unhandled module variable {mod_name}.{attr_name} {attr}")


def generate_stub(mod: ModuleType):
    # generate the module stub
    stub_path = StubPath + "/" + get_module_name(mod).replace(".", "/") + ("/__init__" * hasattr(mod, "__path__")) + ".pyi"
    stub_path_dir = os.path.dirname(stub_path)
    if stub_path_dir:
        os.makedirs(stub_path_dir, exist_ok=True)

    imports = ImportManager()
    contents = StringIO()

    state = State(mod, imports, contents, 0)

    generate_module(mod, state)

    with open(stub_path, "w") as f:
        if mod.__doc__:
            f.write(f'"""{mod.__doc__}"""\n')
        f.write("from __future__ import annotations\n")
        f.write(imports.pack())
        f.write(contents.getvalue())


def load_and_gen_stub(mod: ModuleType):
    generate_stub(mod)

    mod_prefix = f"{mod.__name__}."

    processed_submodules = set()
    if hasattr(mod, "__path__"):
        for sub_module in pkgutil.iter_modules(mod.__path__, mod_prefix):
            try:
                sub_mod = importlib.import_module(sub_module.name)
            except ImportError:
                print(f"Could not import module {sub_module.name}")
            else:
                load_and_gen_stub(sub_mod)
                processed_submodules.add(sub_module.name)
    for sub_mod_name, sub_mod in sys.modules.items():
        if sub_mod_name.startswith(mod_prefix) and sub_mod_name not in processed_submodules:
            load_and_gen_stub(sub_mod)
            processed_submodules.add(sub_mod_name)


def fix_packages(dir_path: str = StubPath):
    for name in os.listdir(dir_path):
        path = os.path.join(dir_path, name)
        if os.path.isdir(path):
            mod_path = path + ".pyi"
            if os.path.isfile(mod_path):
                init_path = os.path.join(path, "__init__.pyi")
                if os.path.isfile(init_path):
                    os.remove(init_path)
                    # raise RuntimeError(f"Module and Init both exist. {mod_path} {init_path}")
                os.rename(mod_path, init_path)
            fix_packages(path)


def main():
    if os.path.isdir(StubPath):
        shutil.rmtree(StubPath)
    load_and_gen_stub(PySide6)
    fix_packages()

    for stub in os.listdir(StubPath):
        base, ext = os.path.splitext(stub)
        os.rename(os.path.join(StubPath, stub), os.path.join(StubPath, f"{base}-stubs{ext}"))

    subprocess.run([sys.executable, "-m", "black", StubPath])


if __name__ == '__main__':
    main()
