import os
import subprocess
import sys
from pathlib import Path
import platform
from tempfile import TemporaryDirectory

from setuptools import setup, Extension, Command
from setuptools.command.build_ext import build_ext

import versioneer

import requirements


def fix_path(path: str) -> str:
    return os.path.realpath(path).replace(os.sep, "/")


cmdclass: dict[str, type[Command]] = versioneer.get_cmdclass()


class CMakeBuild(cmdclass.get("build_ext", build_ext)):
    def build_extension(self, ext):
        import pybind11
        import amulet.pybind11_extensions
        import amulet.io
        import amulet.leveldb
        import amulet.utils
        import amulet.nbt
        import amulet.core
        import amulet.game
        import amulet.anvil
        import amulet.level
        import amulet.resource_pack

        ext_dir = (Path.cwd() / self.get_ext_fullpath("")).parent.resolve()
        src_dir = Path.cwd() / "src" if self.editable_mode else ext_dir

        platform_args = []
        if sys.platform == "win32":
            platform_args.extend(["-G", "Visual Studio 17 2022"])
            if sys.maxsize > 2**32:
                platform_args.extend(["-A", "x64"])
            else:
                platform_args.extend(["-A", "Win32"])
            platform_args.extend(["-T", "v143"])
        elif sys.platform == "darwin":
            if platform.machine() == "arm64":
                platform_args.append("-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64")

        qt6_dir = os.environ.get("QT_ROOT_DIR", None)
        if qt6_dir is None:
            raise RuntimeError(
                "Could not find Qt6 installation. Set QT_ROOT_DIR environment variable."
            )

        if subprocess.run(["cmake", "--version"]).returncode:
            raise RuntimeError("Could not find cmake")
        with TemporaryDirectory() as tempdir:
            if subprocess.run(
                [
                    "cmake",
                    *platform_args,
                    f"-DPYTHON_EXECUTABLE={sys.executable}",
                    f"-DQt6_DIR={qt6_dir}",
                    f"-Dpybind11_DIR={fix_path(pybind11.get_cmake_dir())}",
                    f"-Damulet_pybind11_extensions_DIR={fix_path(amulet.pybind11_extensions.__path__[0])}",
                    f"-Damulet_io_DIR={fix_path(amulet.io.__path__[0])}",
                    f"-Damulet_leveldb_DIR={fix_path(amulet.leveldb.__path__[0])}",
                    f"-Damulet_utils_DIR={fix_path(amulet.utils.__path__[0])}",
                    f"-Damulet_nbt_DIR={fix_path(amulet.nbt.__path__[0])}",
                    f"-Damulet_core_DIR={fix_path(amulet.core.__path__[0])}",
                    f"-Damulet_game_DIR={fix_path(amulet.game.__path__[0])}",
                    f"-Damulet_anvil_DIR={fix_path(amulet.anvil.__path__[0])}",
                    f"-Damulet_level_DIR={fix_path(amulet.level.__path__[0])}",
                    f"-Damulet_resource_pack_DIR={fix_path(amulet.resource_pack.__path__[0])}",
                    f"-DAMULET_EDITOR_SRC_DIR={fix_path(src_dir)}",
                    f"-DAMULET_EDITOR_EXT_SRC_DIR={fix_path(ext_dir)}",
                    f"-DCMAKE_INSTALL_PREFIX=install",
                    "-B",
                    tempdir,
                ]
            ).returncode:
                raise RuntimeError("Error configuring amulet-editor")
            if subprocess.run(
                ["cmake", "--build", tempdir, "--config", "Release"]
            ).returncode:
                raise RuntimeError("Error building amulet-editor")
            if subprocess.run(
                ["cmake", "--install", tempdir, "--config", "Release"]
            ).returncode:
                raise RuntimeError("Error installing amulet-editor")


cmdclass["build_ext"] = CMakeBuild


setup(
    version=versioneer.get_version(),
    cmdclass=cmdclass,
    ext_modules=[
        Extension(
            "builtin_plugins.plugin.amulet.editor.widget._view_3d._view_3d._view_3d", []
        )
    ]
    * (not os.environ.get("AMULET_SKIP_COMPILE", None)),
    install_requires=requirements.get_runtime_dependencies(),
)
