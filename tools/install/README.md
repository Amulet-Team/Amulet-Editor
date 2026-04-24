# Installing from Source

We only recommend installing from source if you want to develop Amulet or can't use a pre-compiled build.

1) Install [Git](https://git-scm.com/) and add it to your path.
2) Install [CMake](https://cmake.org/download/) and add it to your path.
3) Install [Python 3.14](https://www.python.org/downloads/release/python-3144/)
4) Install [Qt 6.11.0 binaries](https://www.qt.io/download-qt-installer-oss) for your platform. Debug symbols are optional but recommended.
5) Install [Visual Studio](https://visualstudio.microsoft.com/) (Windows users only).
6) Copy `install_amulet.py` and `CMakeLists.txt` from this directory and put them in the diretory you want to install Amulet in.
7) Run `install_amulet.py` with Python 3.14. It will download and configure Amulet.
8) Open the project in `_build` with your IDE and compile
   1) The following instructions are only for Windows users.
   2) Open `_build/amulet_meta.sln` in Visual Studio.
   3) Change `Debug` at the top to `RelWithDebInfo`.
   4) Expand `CMakePredefinedTargets` in solution explorer.
   5) Right-click on `INSTALL` and select `Build`.
   6) Wait for the build to finish. This may take a while.
9) Activate `_venv` and run `amulet_editor` to start the app.

This script installs the libraries in editable mode. This means that python code can be modified in-place without reinstalling.
Modifying C++ code requires recompiling, but your IDE will only recompile your code and code that depends on your changes.
If you add or remove C++ files, you will need to reconfigure cmake and then recompile.
