import glob
import os
import sys

# import subprocess
# import logging
import re
import sysconfig

from setuptools import setup, Extension
from distutils import ccompiler
from distutils.sysconfig import get_python_inc
from wheel.bdist_wheel import bdist_wheel

import versioneer
import pybind11

import amulet_nbt
import amulet
import minecraft_model_reader


def get_compile_args() -> list[str]:
    compiler = sysconfig.get_config_var("CXX") or ccompiler.get_default_compiler()
    compile_args = []
    if compiler.split()[0] == "msvc":
        compile_args.append("/std:c++20")
    else:
        compile_args.append("-std=c++20")

    if sys.platform == "darwin":
        compile_args.append("-mmacosx-version-min=10.13")
    return compile_args


CompileArgs = get_compile_args()


# def get_openmp_args() -> tuple[list[str], list[str], list[str], list[str]]:
#     # This has been lifted from here https://github.com/cython/cython/blob/606bd8cf235149c3be6876d0f5ae60032c8aab6c/runtests.py
#     import sysconfig
#     from distutils import ccompiler
#     GCCPattern = re.compile(r"gcc version (?P<major>\d+)\.(?P<minor>\d+)")
#     ClangPattern = re.compile(r"clang(?:-|\s+version\s+)(?P<major>\d+)\.(?P<minor>\d+)")
#
#     def get_openmp_args_for(arg: str) -> tuple[list[str], list[str]]:
#         """arg == 'CC' or 'CXX'"""
#         cc = (
#             sysconfig.get_config_var(arg) or ccompiler.get_default_compiler()
#         ).split()[0]
#         if cc == "msvc":
#             # Microsoft Visual C
#             return ["/openmp"], []
#         elif cc:
#             # Try GCC and Clang
#             try:
#                 out = subprocess.check_output([cc, "-v"]).decode()
#             except ChildProcessError:
#                 logging.exception(f"Could not resolve unknown compiler {cc}")
#             else:
#                 gcc_match = GCCPattern.search(out)
#                 if gcc_match:
#                     if (gcc_match.group("major"), gcc_match.group("minor")) >= (4, 2):
#                         return ["-fopenmp"], ["-fopenmp"]
#                     return [], []
#                 clang_match = ClangPattern.search(out)
#                 if clang_match:
#                     # if (clang_match.group("major"), clang_match.group("minor")) >= (3, 7):
#                     #     return ['-fopenmp'], ['-fopenmp']
#                     return [], []
#         # If all else fails disable openmp
#         return [], []
#
#     omp_ccargs, omp_clargs = get_openmp_args_for("CC")
#     omp_cppcargs, omp_cpplargs = get_openmp_args_for("CXX")
#
#     return omp_ccargs, omp_clargs, omp_cppcargs, omp_cpplargs


cmdclass = versioneer.get_cmdclass()
BDistWheelOriginal: type[bdist_wheel] = cmdclass.get("bdist_wheel", bdist_wheel)


class BDistWheel(BDistWheelOriginal):
    def finalize_options(self) -> None:
        # Freeze requirements so that the same version is installed as was compiled against.
        frozen_requirements = {
            "amulet_nbt": amulet_nbt.__version__,
            "amulet_core": amulet.__version__,
            "minecraft_resource_pack": minecraft_model_reader.__version__,
        }
        install_requires = list(self.distribution.install_requires)
        for i, requirement in enumerate(self.distribution.install_requires):
            match = re.match(r"[a-zA-Z0-9_-]+", requirement)
            if match is None:
                continue
            name = match.group().lower().replace("-", "_")
            if name not in frozen_requirements:
                continue
            install_requires[i] = f"{name}=={frozen_requirements.pop(name)}"

        if frozen_requirements:
            raise RuntimeError(f"{frozen_requirements} {install_requires}")

        self.distribution.install_requires = install_requires
        super().finalize_options()


cmdclass["bdist_wheel"] = BDistWheel


AmuletNBTLib = (
    "amulet_nbt",
    dict(
        sources=glob.glob(
            os.path.join(glob.escape(amulet_nbt.get_source()), "**", "*.cpp"),
            recursive=True,
        ),
        include_dirs=[amulet_nbt.get_include()],
        cflags=CompileArgs,
    ),
)

AmuletCoreLib = (
    "amulet_core",
    dict(
        sources=glob.glob(
            os.path.join(glob.escape(amulet.__path__[0]), "**", "*.cpp"),
            recursive=True,
        ),
        include_dirs=[
            get_python_inc(),
            pybind11.get_include(),
            amulet_nbt.get_include(),
            os.path.dirname(amulet.__path__[0]),
        ],
        cflags=CompileArgs,
    ),
)


setup(
    version=versioneer.get_version(),
    cmdclass=cmdclass,
    libraries=[AmuletNBTLib, AmuletCoreLib],
    ext_modules=[
        Extension(
            name="builtin_plugins.amulet_team_3d_viewer._view_3d._chunk_builder",
            sources=[
                "src/builtin_plugins/amulet_team_3d_viewer/_view_3d/_chunk_builder.cpp",
                "src/builtin_plugins/amulet_team_3d_viewer/_view_3d/_chunk_builder.py.cpp",
            ],
            include_dirs=[
                pybind11.get_include(),
                amulet_nbt.get_include(),
                os.path.dirname(amulet.__path__[0]),
                "src",
                "src/builtin_plugins",
            ],
            libraries=["amulet_nbt", "amulet_core"],
            define_macros=[("PYBIND11_DETAILED_ERROR_MESSAGES", None)],
            extra_compile_args=CompileArgs,
        ),
    ],
)
