"""This generates a Visual Studio solution file and projects for each module."""

import os
import pybind11
import pybind11_extensions
from shared.generate_vs_sln import (
    get_package_path,
    ProjectData,
    CompileMode,
    get_files,
    PythonIncludeDir,
    PythonLibraryDir,
    write,
)

SrcDir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")


def main() -> None:
    amulet_nbt_path = get_package_path("amulet_nbt")
    amulet_nbt_lib = ProjectData(
        name="amulet_nbt",
        compile_mode=CompileMode.StaticLibrary,
        include_files=get_files(
            root_dir=amulet_nbt_path, root_dir_suffix="include", ext="hpp"
        ),
        source_files=get_files(
            root_dir=amulet_nbt_path, root_dir_suffix="cpp", ext="cpp"
        ),
        include_dirs=[os.path.join(amulet_nbt_path, "include")],
    )
    amulet_nbt_py = ProjectData(
        name="__init__",
        compile_mode=CompileMode.PythonExtension,
        source_files=get_files(
            root_dir=amulet_nbt_path,
            root_dir_suffix="pybind",
            ext="cpp",
        ),
        include_dirs=[
            PythonIncludeDir,
            pybind11.get_include(),
            pybind11_extensions.get_include(),
            os.path.join(amulet_nbt_path, "include"),
        ],
        library_dirs=[
            PythonLibraryDir,
        ],
        dependencies=[
            amulet_nbt_lib,
        ],
        py_package="amulet_nbt",
        package_dir=os.path.dirname(amulet_nbt_path),
    )

    amulet_core_path = get_package_path("amulet")
    amulet_core_lib = ProjectData(
        name="amulet",
        compile_mode=CompileMode.StaticLibrary,
        include_files=get_files(
            root_dir=os.path.dirname(amulet_core_path),
            root_dir_suffix="amulet",
            ext="hpp",
            exclude_exts=[".py.hpp"],
        ),
        source_files=get_files(
            root_dir=os.path.dirname(amulet_core_path),
            root_dir_suffix="amulet",
            ext="cpp",
            exclude_exts=[".py.cpp"],
        ),
        include_dirs=[
            PythonIncludeDir,
            pybind11.get_include(),
            pybind11_extensions.get_include(),
            os.path.join(amulet_nbt_path, "include"),
            os.path.dirname(amulet_core_path),
        ],
    )
    amulet_core_py = ProjectData(
        name="__init__",
        compile_mode=CompileMode.PythonExtension,
        include_files=get_files(
            root_dir=os.path.dirname(amulet_core_path),
            root_dir_suffix="amulet",
            ext="py.hpp",
        ),
        source_files=get_files(
            root_dir=os.path.dirname(amulet_core_path),
            root_dir_suffix="amulet",
            ext="py.cpp",
        ),
        include_dirs=[
            PythonIncludeDir,
            pybind11.get_include(),
            pybind11_extensions.get_include(),
            os.path.join(amulet_nbt_path, "include"),
            os.path.dirname(amulet_core_path),
        ],
        library_dirs=[
            PythonLibraryDir,
        ],
        dependencies=[amulet_nbt_lib, amulet_core_lib],
        py_package="amulet",
        package_dir=os.path.dirname(amulet_core_path),
    )

    view_3d_path = os.path.join(
        SrcDir, "builtin_plugins", "amulet_team_3d_viewer", "_view_3d"
    )
    chunk_builder_py = ProjectData(
        name="__init__",
        compile_mode=CompileMode.PythonExtension,
        include_files=get_files(root_dir=view_3d_path, ext="hpp"),
        source_files=get_files(
            root_dir=view_3d_path,
            ext="cpp",
        ),
        include_dirs=[
            PythonIncludeDir,
            pybind11.get_include(),
            pybind11_extensions.get_include(),
            os.path.join(amulet_nbt_path, "include"),
            os.path.dirname(amulet_core_path),
            view_3d_path,
        ],
        library_dirs=[
            PythonLibraryDir,
        ],
        dependencies=[amulet_nbt_lib, amulet_core_lib],
        py_package="builtin_plugins.amulet_team_3d_viewer._view_3d",
    )
    projects = [
        amulet_nbt_lib,
        amulet_nbt_py,
        amulet_core_lib,
        amulet_core_py,
        chunk_builder_py,
    ]

    write(
        SrcDir,
        os.path.join(SrcDir, "sln"),
        "Amulet-Editor",
        projects,
    )


if __name__ == "__main__":
    main()
