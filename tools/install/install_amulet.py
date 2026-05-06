def main() -> None:
    import subprocess
    import sys
    import venv
    import os
    import sysconfig
    import platform
    import shutil

    # Check environment
    if sys.version_info[:2] != (3, 14):
        raise Exception("This script must be run with Python 3.14")

    if subprocess.run(["git", "--version"], capture_output=True).returncode:
        raise RuntimeError("Could not find git")

    if subprocess.run(["cmake", "--version"], capture_output=True).returncode:
        raise RuntimeError("Could not find cmake")

    def fix_path(path: str | os.PathLike[str]) -> str:
        return os.path.realpath(path).replace(os.sep, "/")

    # Clone repositories
    for repo, branch in [
        ("Amulet-Test-Utils", "main"),
        ("Amulet-pybind11-extensions", "main"),
        ("Amulet-IO", "2.0"),
        ("Amulet-LevelDB", "3.0"),
        ("Amulet-Utils", "1.0"),
        ("Amulet-zlib", "1.0"),
        ("Amulet-NBT", "5.0"),
        ("Amulet-Core", "2.0"),
        ("Amulet-Game", "1.0"),
        ("Amulet-Anvil", "1.0"),
        ("Amulet-Level", "1.0"),
        ("Amulet-Resource-Pack", "1.0"),
        ("Amulet-Editor", "1.0"),
    ]:
        if not os.path.isdir(repo):
            if subprocess.run(
                ["git", "clone", f"https://github.com/Amulet-Team/{repo}"]
            ).returncode:
                raise RuntimeError(f"Could not clone {repo}")
            if subprocess.run(["git", "-C", repo, "switch", branch]).returncode:
                raise RuntimeError(f"Could not switch to branch {branch} of {repo}")

    venv_dir = "_venv"
    if not os.path.isdir(venv_dir):
        env = venv.EnvBuilder(with_pip=True, symlinks=True)
        env.create(venv_dir)

    python_path = os.path.join(
        venv_dir, *(("Scripts", "python.exe") if os.name == "nt" else ("bin", "python"))
    )

    # Install repositories without compiling C++
    if subprocess.run(
        [
            python_path,
            "-m",
            "pip",
            "install",
            "-e",
            "./Amulet-pybind11-extensions",
            "-e",
            "./Amulet-IO",
            "-e",
            "./Amulet-LevelDB",
            "-e",
            "./Amulet-Utils",
            "-e",
            "./Amulet-zlib",
            "-e",
            "./Amulet-NBT",
            "-e",
            "./Amulet-Core",
            "-e",
            "./Amulet-Game",
            "-e",
            "./Amulet-Anvil",
            "-e",
            "./Amulet-Level",
            "-e",
            "./Amulet-Resource-Pack",
            "-e",
            "./Amulet-Editor",
        ],
        env={**os.environ, "AMULET_SKIP_COMPILE": "1"},
    ).returncode:
        raise RuntimeError("Could not install requirements")

    # Setup C++ Project
    platform_args = []
    if sys.platform == "win32":
        platform_args.extend(["-G", "Visual Studio 17 2022"])
        if sysconfig.get_platform() == "win-amd64":
            platform_args.extend(["-A", "x64"])
        elif sysconfig.get_platform() == "win32":
            platform_args.extend(["-A", "Win32"])
        elif sysconfig.get_platform() == "win-arm64":
            platform_args.extend(["-A", "ARM64"])
        else:
            raise RuntimeError(f"Unsupported platform: {{sysconfig.get_platform()}}")
        platform_args.extend(["-T", "v143"])
    elif sys.platform == "darwin":
        if platform.machine() == "arm64":
            platform_args.append("-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64")

    p = subprocess.run(
        [python_path, "-c", "import pybind11;print(pybind11.get_cmake_dir())"],
        text=True,
        capture_output=True,
    )
    if p.returncode:
        raise RuntimeError("Could not find pybind11")
    pybind11_path = p.stdout.strip()

    qt6_dir = input(
        "Enter the path to Qt6 cmake files. E.g. C:/Qt/6.10.3/msvc2022_64/lib/cmake/Qt6: "
    )

    shutil.rmtree(os.path.join("_build", "CMakeFiles"), ignore_errors=True)
    if subprocess.run(
        [
            "cmake",
            *platform_args,
            f"-DPython3_EXECUTABLE={fix_path(python_path)}",
            f"-DCMAKE_INSTALL_PREFIX=_install",
            f"-DQt6_DIR={fix_path(qt6_dir)}",
            f"-Dpybind11_DIR={fix_path(pybind11_path)}",
            "-B",
            "_build",
        ]
    ).returncode:
        raise RuntimeError("Error configuring amulet-editor")


if __name__ == "__main__":
    try:
        main()
    except:
        import traceback

        traceback.print_exc()
        input("Press Enter to exit")
