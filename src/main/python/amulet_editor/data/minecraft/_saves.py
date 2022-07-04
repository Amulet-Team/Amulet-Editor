import os


def locate_file(file: str, directory: str, recursive=False) -> list[str]:
    """
    Returns a list of all paths containing the specified file within
    the specified directory.
    """

    paths: list[str] = []
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)) and item == file:
            paths.append(directory + item)
        elif recursive and os.path.isdir(directory + item):
            locate_file(file, directory + item, paths)

    return paths


def locate_levels(directories: list[str]) -> list[str]:
    """
    Returns a list of paths to all identified minecraft level.dat
    files in the list of provided directories.
    """

    worlds: list[str] = []

    for directory in directories:
        for folder in os.listdir(directory):
            folder = os.path.join(directory, folder)
            if os.path.exists(os.path.join(folder, "level.dat")):
                worlds.append(os.path.join(folder))

    return worlds
