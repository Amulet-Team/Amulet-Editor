import os

from PySide6.QtCore import QStandardPaths


DefaultDataDir = os.path.join(
    QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
    "AmuletTeam",
    "AmuletEditor",
    "data",
)
DefaultConfigDir = os.path.join(
    QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
    "AmuletTeam",
    "AmuletEditor",
    "config",
)
DefaultCacheDir = os.path.join(
    QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
    "AmuletTeam",
    "AmuletEditor",
    "cache",
)
DefaultLogDir = os.path.join(
    QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation),
    "AmuletTeam",
    "AmuletEditor",
    "logs",
)


def _init_paths(
    data_dir: str | None,
    config_dir: str | None,
    cache_dir: str | None,
    log_dir: str | None,
) -> None:
    if data_dir is None:
        os.environ.setdefault("DATA_DIR", DefaultDataDir)
    else:
        os.environ["DATA_DIR"] = data_dir

    if config_dir is None:
        os.environ.setdefault("CONFIG_DIR", DefaultConfigDir)
    else:
        os.environ["CONFIG_DIR"] = config_dir

    if cache_dir is None:
        os.environ.setdefault("CACHE_DIR", DefaultCacheDir)
    else:
        os.environ["CACHE_DIR"] = cache_dir

    if log_dir is None:
        os.environ.setdefault("LOG_DIR", DefaultLogDir)
    else:
        os.environ["LOG_DIR"] = log_dir


def data_directory() -> str:
    """
    Returns a path to the directory used for storage of persistent data.
    Generates appropriate directories if path does not already exist.
    """
    directory = os.environ["DATA_DIR"]
    os.makedirs(directory, exist_ok=True)
    return directory


def config_directory() -> str:
    """
    Returns a path to the directory used for storage of configuration data.
    Generates appropriate directories if path does not already exist.
    """
    directory = os.environ["CONFIG_DIR"]
    os.makedirs(directory, exist_ok=True)
    return directory


def cache_directory() -> str:
    """
    Returns a path to the directory used for storage of cache data.
    Generates appropriate directories if path does not already exist.
    """
    directory = os.environ["CACHE_DIR"]
    os.makedirs(directory, exist_ok=True)
    return directory


def logging_directory() -> str:
    """
    Returns a path to the directory used for storage of logging data.
    Generates appropriate directories if path does not already exist.
    """
    directory = os.environ["LOG_DIR"]
    os.makedirs(directory, exist_ok=True)
    return directory


def user_directory() -> str:
    directory = os.path.join(data_directory(), "user")
    os.makedirs(directory, exist_ok=True)

    return directory


def project_directory(project_name: str | None = None) -> str:
    """Returns a path to the default location for storing Amulet projects."""

    documents = os.path.normpath(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
    )

    directory = os.path.join(
        documents,
        "Amulet",
        "projects",
    )

    if project_name is not None:
        directory = os.path.join(directory, project_name)

    os.makedirs(directory, exist_ok=True)
    return directory
