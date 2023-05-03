import argparse
import logging
import subprocess
import sys
from typing import Protocol, Optional


BROKER = "BROKER"


class Args(Protocol):
    level_path: Optional[str]
    logging_level: int
    logging_format: str


_args = None


def parse_args() -> Args:
    global _args

    if _args is None:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--level_path",
            type=str,
            help="The Minecraft world or structure to open. Default opens no level",
            action="store",
            dest="level_path",
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

        _args, _ = parser.parse_known_args()

    return _args


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
    subprocess.Popen(
        new_args,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
