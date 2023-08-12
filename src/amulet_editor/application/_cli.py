import argparse
import logging
import subprocess
import sys
from typing import Protocol, Optional
from amulet_editor.data.paths._application import (
    DefaultDataDir,
    DefaultConfigDir,
    DefaultCacheDir,
    DefaultLogDir,
)


BROKER = "BROKER"


class Args(Protocol):
    level_path: Optional[str]
    data_dir: Optional[str]
    config_dir: Optional[str]
    cache_dir: Optional[str]
    log_dir: Optional[str]
    logging_level: int
    logging_format: str
    trace: bool


_args: Optional[Args] = None


def parse_args() -> Args:
    global _args

    if _args is None:
        parser = argparse.ArgumentParser(
            prog="Amulet Editor",
            description="Amulet is a Minecraft world editing application.",
            epilog="The following arguments are a subset of the full arguments.",
        )

        parser.add_argument(
            "--level_path",
            type=str,
            help="The Minecraft world or structure to open. Default opens no level",
            action="store",
            dest="level_path",
            default=None,
        )

        parser.add_argument(
            "--data_dir",
            type=str,
            help=f"The directory to store application data in. Default is {DefaultDataDir}",
            action="store",
            dest="data_dir",
            default=None,
        )

        parser.add_argument(
            "--config_dir",
            type=str,
            help=f"The directory to store application config files in. Default is {DefaultConfigDir}",
            action="store",
            dest="config_dir",
            default=None,
        )

        parser.add_argument(
            "--cache_dir",
            type=str,
            help=f"The directory to store cache files in. Default is {DefaultCacheDir}",
            action="store",
            dest="cache_dir",
            default=None,
        )

        parser.add_argument(
            "--log_dir",
            type=str,
            help=f"The directory to store log files in. Default is {DefaultLogDir}",
            action="store",
            dest="log_dir",
            default=None,
        )

        parser.add_argument(
            "--logging_level",
            type=int,
            help="The logging level to set. CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10. Default is WARNING",
            action="store",
            dest="logging_level",
            default=logging.WARNING,
        )

        parser.add_argument(
            "--logging_format",
            type=str,
            help='The logging format to use. Default is "%(levelname)s - %(message)s"',
            action="store",
            dest="logging_format",
            default="%(levelname)s - %(message)s",
        )

        parser.add_argument(
            "--trace",
            help="If defined, print the qualified name of each function as it is called. Useful if the program crashes due to an access violation and you don't know where it came from.",
            action="store_true",
            dest="trace",
        )

        _args, _ = parser.parse_known_args()

    return _args  # noqa


# TODO: move this somewhere more sensible
def spawn_process(path: str = None):
    """Spawn the broker process passing over the input CLI values."""
    this_args = parse_args()
    new_args = [sys.executable, sys.argv[0]]
    if path is not None:
        new_args += ["--level_path", path]
    new_args += [
        "--logging_level",
        str(this_args.logging_level),
        "--logging_format",
        this_args.logging_format,
    ]
    if this_args.trace:
        new_args.append("--trace")
    subprocess.Popen(
        new_args,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
