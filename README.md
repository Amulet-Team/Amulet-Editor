# Amulet-Editor

## Running from Source
To run Amulet Editor from source, it is recommended to install Visual Studio Code though not required.

First, install the base requirements for Amulet Editor. Requirements are separated out by platform: Windows, Mac, and Linux and can be installed via the command: `pip install -r .\requirements\windows.txt` replacing `windows` with `mac` or `linux` depending on which of the platforms you are using.

If using fbs, you should additionally install fbs-pro version 1.1.0 or an equivalent, but note that fbs-pro is a paid software available here: (https://build-system.fman.io/pro).

Once all requirements are installed, you should be able to select the new environment as your default environment in Visual Studio Code and run the project using the `Run Without Debugging` command from the `Run` tab in the menu bar. Alternatively, you can use the shortcut `F5` (default, may vary on your system) to launch the application.

If not using Visual Studio Code, you should be able to run Amulet Editor in the terminal by activating the virtual environment you created and running the command `py -m amulet_editor` or `fbs run` if you have fbs installed as well.
