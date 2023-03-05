"""
There are some issues with the stub files distributed with PySide6 which make development difficult.
This script will modify the stub files to fix some of those issues.
"""

from __future__ import annotations

import re
import typing
from typing import Optional, overload
import inspect
import os
from enum import EnumType, Enum
import pkgutil
import importlib
from types import ModuleType
from io import StringIO
import sys
import shutil
import subprocess
from contextlib import contextmanager, suppress

import PySide6
from PySide6.QtCore import Signal
from PySide6.support.signature.mapping import ArrayLikeVariable, Default, Instance, Invalid

StubPath = "stubs"

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

Void1 = object()
Void2 = object()


BuiltInClassAttrs = {
    "__abstractmethods__",
    "__annotations__",
    "__base__",
    "__bases__",
    "__basicsize__",
    "__class__",
    "__copy__",
    "__delattr__",
    "__dict__",
    "__dictoffset__",
    "__dir__",
    "__doc__",
    "__flags__",
    "__getattribute__",
    "__init_subclass__",
    "__instancecheck__",
    "__isabstractmethod__",
    "__itemsize__",
    "__members__",
    "__module__",
    "__mro__",
    "__name__",
    "__new__",
    "__opaque_container__",
    "__prepare__",
    "__qualname__",
    "__repr__",
    "__setattr__",
    "__signature__",
    "__subclasshook__",
    "__text_signature__",
    "__weakrefoffset__",
}

BuiltInModuleAttrs = {
    "__doc__",
    "__file__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}

PySide6Map: dict[str, list[str]] = {}


def _generate_pyside6_map(mod):
    for sub_module in pkgutil.iter_modules(mod.__path__, f"{mod.__name__}."):
        try:
            sub_mod = importlib.import_module(sub_module.name)
        except ImportError:
            print(f"Could not import module {sub_module.name}")
        else:
            for name in dir(sub_mod):
                PySide6Map.setdefault(name, []).append(sub_mod.__name__)


_generate_pyside6_map(PySide6)


class ImportManager:
    def __init__(self):
        self._attrs: dict[str, set[tuple[str, str]]] = {}
        # self._hidden_attrs: dict[str, set[tuple[str, str]]] = {}
        self._mods: dict[str, set[str]] = {}

    def import_attr(self, mod_name: str, attr: str, alias: str = None):
        if alias is None:
            alias = attr
        if not alias.isidentifier():
            raise RuntimeError(alias)
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
def get_module_qualname(obj) -> tuple[Optional[str], str]:
    ...

def get_module_qualname(obj):
    """Get the module the object was defined in and the qualified name within that module."""
    # Get the qualified name from the object
    qualname = getattr(obj, "__qualname__", None) or obj.__class__.__qualname__

    if isinstance(obj, Enum):
        qualname += f".{obj.name}"

    # Find the module name
    module_name = None

    if obj in (int, float, str, list, dict, tuple) or isinstance(obj, (int, float, str, list, dict, tuple)):
        module_name = obj.__class__.__module__
    elif obj is None:
        module_name = "builtins"
    elif inspect.ismodule(obj):
        module_name = obj.__name__
    else:
        for func in (
            lambda: obj.__module__,
            lambda: obj.__objclass__.__module__,
            lambda: obj.__self__.__module__
        ):
            if module_name is not None:
                break
            with suppress(AttributeError):
                module_name = func()

    if module_name is not None:
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


def get_module_name(obj) -> Optional[str]:
    """Get the module name where this object was defined."""
    return get_module_qualname(obj)[0]


def get_qualname(obj) -> Optional[str]:
    return get_module_qualname(obj)[1]


def get_name(obj) -> str:
    return getattr(obj, "__name__", None) or obj.__class__.__name__


def get_path(obj) -> tuple[Optional[str], Optional[str], str]:
    mod, qual = get_module_qualname(obj)
    return mod, qual, get_name(obj)


def get_module(obj) -> Optional[ModuleType]:
    mod_name = get_module_name(obj)
    return None if mod_name is None else importlib.import_module(mod_name)


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


class Stub:
    def __init__(self, module: ModuleType):
        self._module = module
        self._imports = ImportManager()
        self._contents = StringIO()
        self._indentation = 0

    @contextmanager
    def _indent(self):
        self._indentation += 1
        yield
        self._indentation -= 1

    @classmethod
    def generate(cls, module: ModuleType):
        Stub(module)._generate()

    def _generate(self):
        self._generate_stub()

        mod_prefix = f"{self._module.__name__}."

        processed_submodules = set()
        if hasattr(self._module, "__path__"):
            for sub_module in pkgutil.iter_modules(self._module.__path__, mod_prefix):
                try:
                    sub_mod = importlib.import_module(sub_module.name)
                except ImportError:
                    print(f"Could not import module {sub_module.name}")
                else:
                    Stub.generate(sub_mod)
                    processed_submodules.add(sub_module.name)
        for sub_mod_name, sub_mod in sys.modules.items():
            if sub_mod_name.startswith(mod_prefix) and sub_mod_name not in processed_submodules:
                Stub.generate(sub_mod)
                processed_submodules.add(sub_mod_name)

    def _generate_stub(self):
        # generate the module stub
        stub_path = StubPath + "/" + get_module_name(self._module).replace(".", "/") + ("/__init__" * hasattr(self._module, "__path__")) + ".pyi"
        stub_path_dir = os.path.dirname(stub_path)
        if stub_path_dir:
            os.makedirs(stub_path_dir, exist_ok=True)

        self._generate_module()

        with open(stub_path, "w") as f:
            if self._module.__doc__:
                f.write(f'"""{self._module.__doc__}"""\n')
            f.write("from __future__ import annotations\n")
            f.write(self._imports.pack())
            f.write(self._contents.getvalue())

    def _generate_module(self):
        for attr_name in dir(self._module):
            if attr_name in BuiltInModuleAttrs:
                continue
            # if attr_name.startswith("_"):
            #     continue
            attr = getattr(self._module, attr_name)
            self._generate_attr(self._module, "", attr_name, attr)

    def _generate_class(self, cls: type):
        superclasses = []
        for superclass in cls.__bases__:
            if superclass is object or superclass is type:
                continue
            mod_name, qualname, name = get_path(superclass)
            if mod_name == "builtins":
                superclasses.append(qualname)
            elif mod_name is None:
                raise RuntimeError
            else:
                superclasses.append(f"{mod_name}.{qualname}")
            self._imports.import_module(mod_name)

        sup = f"({', '.join(superclasses)})" if superclasses else ""
        self._contents.write(f"{Indent * self._indentation}class {cls.__name__}{sup}:\n")
        start = self._contents.tell()

        with self._indent():
            for attr_name in dir(cls):
                if attr_name in BuiltInClassAttrs:
                    continue
                elif attr_name in {"from"}:
                    # Uncallable from python
                    self._contents.write(f"{Indent * self._indentation}# {attr_name} = Any\n")
                    continue

                attr = getattr(cls, attr_name)
                self._generate_attr(cls, cls.__qualname__, attr_name, attr)

        if start == self._contents.tell():
            self._contents.write(f"{Indent * self._indentation}\tpass\n")
        self._contents.write("\n\n")

    def _generate_attr(self, container, context: str, attr_name: str, attr):
        """
        Generate the documentation for an attribute
        :param context: The qualified name prefix.
        :param attr_name: The name the attribute was found at in this module.
        :param attr: The attribute to generate docs for.
        """
        local_qualname = f"{context}.{attr_name}" if context else attr_name
        defmod_name, qualname = get_module_qualname(attr)
        defmod_name = defmod_name or self._module.__name__
        defmod = get_module(attr)
        super_attr = Void1
        for base in getattr(container, "__bases__", []):
            super_attr = getattr(base, attr_name, Void1)
            if super_attr is not Void1:
                break

        if super_attr is attr or get_module_qualname(super_attr) == get_module_qualname(attr):
            # Defined in parent
            pass
        elif attr is None:
            self._contents.write(f"{Indent * self._indentation}{attr_name} = None\n")
        elif isinstance(attr, Enum):
            if inspect.isclass(container) and isinstance(attr, container):
                self._contents.write(f"{Indent * self._indentation}{attr_name} = {attr.value}\n")
            else:
                self._imports.import_module(defmod_name)
                self._contents.write(f"{Indent * self._indentation}{attr_name} = {defmod_name}.{qualname}\n")
        elif isinstance(attr, (bool, float, int)):
            self._contents.write(f"{Indent * self._indentation}{attr_name} = {attr}\n")
        elif isinstance(attr, str):
            self._contents.write(f"{Indent * self._indentation}{attr_name} = \"{attr}\"\n")
        elif inspect.ismodule(attr):
            self._imports.import_module(attr.__name__, local_qualname)
        elif isinstance(attr, Signal):
            self._contents.write(f"{Indent * self._indentation}{attr_name} = {self._format_signal(attr)}\n")
        elif inspect.isclass(attr) or inspect.isfunction(attr) or inspect.ismethod(attr) or inspect.ismethoddescriptor(attr) or inspect.isbuiltin(attr):
            # if inspect.isclass(container) and hasattr(super(container, container), attr_name)
            if defmod is None or defmod is self._module:
                if local_qualname == qualname:
                    # This is the definition
                    if inspect.isclass(attr):
                        self._generate_class(attr)
                    elif inspect.isfunction(attr) or inspect.ismethod(attr) or inspect.ismethoddescriptor(attr) or inspect.isbuiltin(attr):
                        self._generate_callable(attr)
                else:
                    # Alias from the same module
                    self._imports.import_module(self._module.__name__)
                    self._contents.write(f"{Indent * self._indentation}{attr_name} = {defmod_name}.{qualname}\n")
            else:
                self._imports.import_attr(defmod_name, attr.__name__, local_qualname)
        else:
            self._imports.import_attr("typing", "Any")
            self._contents.write(f"{Indent * self._indentation}{attr_name} = Any  # 5\n")
            print(f"unhandled module variable {self._module.__name__}.{local_qualname} {attr}")

    def _format_signal(self, signal: Signal) -> str:
        if not isinstance(signal, Signal):
            raise TypeError
        self._imports.import_attr("PySide6.QtCore", "Signal")
        match = re.fullmatch(r"[_a-zA-Z0-9]*\((?P<args>.*)\)", str(signal))
        if match is None:
            raise RuntimeError(str(signal))

        args = match.group("args")
        fixed_args = self._split_and_fix_args(args)
        return f"Signal({', '.join(fixed_args)})"

    def _split_and_fix_args(self, a: str) -> list[str]:
        args = []
        bracket_count = 0
        start_index = 0
        index = 0
        for index, c in enumerate(a):
            if c in "({[<":
                bracket_count += 1
            elif c in ")}]>":
                bracket_count -= 1
            elif c == "," and bracket_count == 0:
                args.append(self._import_and_fix_string_type(a[start_index:index].strip()))
                start_index = index + 1
        if index:
            args.append(self._import_and_fix_string_type(a[start_index:index + 1].strip()))
        return args

    def _import_and_fix_string_type(self, t: str) -> str:
        match = re.fullmatch(r"(const )?(?P<name>[a-zA-Z0-9_]+(::[a-zA-Z0-9_]+)*)(<(?P<template>[a-zA-Z0-9_:*&,<>]*?)>)?[*&]?", t)

        if match is None:
            raise RuntimeError

        t = match.group("name").replace("::", ".")
        template = match.group("template")

        if t == "QString":
            return "str"
        elif t == "QList" and template:
            return f"list[{self._split_and_fix_args(template)}]"
        elif t in {"QHash", "QMultiMap"}:
            return f"dict[{self._split_and_fix_args(template)}]"
        elif template:
            raise RuntimeError

        self._find_and_import_pyside6(t)

        return t

    def _find_and_import_pyside6(self, t: str):
        if t not in {"float", "int", "str", "bool"}:
            name = t.split(".")[0]
            if name in PySide6Map:
                self._imports.import_attr(PySide6Map[name][0], name)

    def _generate_callable(self, func):
        indent = "    " * self._indentation
        try:
            signature = getattr(func, "__signature__", None) or inspect.signature(func)
        except ValueError:
            if inspect.ismethod(func) or inspect.ismethoddescriptor(func) or inspect.ismethodwrapper(func):
                self._contents.write(f"{indent}def {func.__name__}(self, *args, **kwargs):...\n")
            elif inspect.isbuiltin(func):
                self._contents.write(f"{indent}@staticmethod\n{indent}def {func.__name__}(*args, **kwargs):...\n")
            else:
                self._contents.write(f"{indent}def {func.__name__}(*args, **kwargs):...\n")
        else:
            if isinstance(signature, list) and len(signature) == 1:
                signature = signature[0]

            if isinstance(signature, inspect.Signature):
                if inspect.isbuiltin(func):
                    self._contents.write(f"{indent}@staticmethod\n{indent}def {func.__name__}{self._stringify_signature(signature)}:...\n")
                else:
                    self._contents.write(f"{indent}def {func.__name__}{self._stringify_signature(signature)}:...\n")
            elif isinstance(signature, list):
                for sig in signature:
                    if not isinstance(sig, inspect.Signature):
                        raise RuntimeError
                    if inspect.isbuiltin(func):
                        self._contents.write(f"{indent}@overload\n{indent}@staticmethod\n{indent}def {func.__name__}{self._stringify_signature(sig)}:...\n")
                    else:
                        self._contents.write(f"{indent}@overload\n{indent}def {func.__name__}{self._stringify_signature(sig)}:...\n")
                self._imports.import_attr("typing", "overload")
            else:
                raise TypeError

    def _stringify_signature(self, signature: inspect.Signature) -> str:
        replace = {}

        params = dict(signature.parameters)
        for param_name in list(params):
            param = params[param_name]
            self._streamline_type(param.annotation, replace)
            default = param.default
            if isinstance(default, (Default, Instance, Invalid)) or default is int or (inspect.isclass(default) and issubclass(default, (Enum, EnumType))) or default is PySide6.support.signature.mapping.ellipsis:
                params[param_name] = param.replace(default=Ellipsis)
            elif isinstance(default, (Enum,)):
                params[param_name] = param.replace(default=default.value)
            elif default is param.empty or default is None or isinstance(default, (int, str, float, dict, list, PySide6.QtCore.QCborTag, PySide6.QtCore.QRect)):
                self._streamline_type(param.default, replace)
            else:
                self._streamline_type(param.default, replace)

        signature = inspect.Signature(parameters=list(params.values()), return_annotation=signature.return_annotation)

        self._streamline_type(signature.return_annotation, replace)

        signature_str = str(signature)

        for short, full in replace.items():
            signature_str = signature_str.replace(full, short)

        signature_str = re.sub(r"\bNoneType\b", "None", signature_str)

        if signature_str.endswith(" -> None"):
            signature_str = signature_str[:-8]

        return signature_str

    def _streamline_type(self, obj, replace: dict[str, str]):
        if obj is None or obj is inspect.Signature.empty:
            return
        # elif isinstance(obj, (Default, Instance, Invalid)):
        #     replace[repr(obj)] = "..."
        #     return
        mod_name, qualname, name = get_path(obj)
        if mod_name == "builtins":
            return
        elif mod_name is None:
            raise RuntimeError
        elif mod_name.startswith("shibokensupport"):
            replace["shibokensupport"] = "PySide6.support"

        if mod_name in {"typing"}:
            self._imports.import_attr(mod_name, name)
        else:
            self._imports.import_module(mod_name)

        self._streamline_args(typing.get_args(obj), replace)

    def _streamline_args(self, obj, replace: dict[str, str]):
        if isinstance(obj, (list, tuple)):
            for arg in obj:
                self._streamline_args(typing.get_args(arg), replace)
        else:
            self._streamline_type(obj, replace)


def generate_stubs(*modules: ModuleType):
    if os.path.isdir(StubPath):
        shutil.rmtree(StubPath)

    for module in modules:
        Stub.generate(module)

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

    fix_packages()

    for stub in os.listdir(StubPath):
        base, ext = os.path.splitext(stub)
        os.rename(os.path.join(StubPath, stub), os.path.join(StubPath, f"{base}-stubs{ext}"))

    subprocess.run([sys.executable, "-m", "black", StubPath])


def main():
    generate_stubs(PySide6)


if __name__ == '__main__':
    main()
