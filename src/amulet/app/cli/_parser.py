from argparse import ArgumentParser, REMAINDER, OPTIONAL
import logging
from collections.abc import Sequence
import sys

from amulet.app.path._application import (
    DefaultDataDir,
    DefaultConfigDir,
    DefaultCacheDir,
    DefaultLogDir,
)

from ._args import CLIArgs


def parse_cli(
    argv: Sequence[str] | None = None,
    valid_commands: Sequence[str] | None = None,
) -> CLIArgs:
    parser = ArgumentParser(
        prog="amulet_editor",
        add_help=False,
        description="Amulet is a Minecraft world editing application.",
    )

    parser.add_argument(
        "-h",
        "--help",
        help="Show this help message and exit.",
        action="store_true",
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
        help="The logging level to set. CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10. Default is INFO",
        action="store",
        dest="logging_level",
        default=logging.INFO,
    )

    parser.add_argument(
        "--logging_format",
        type=str,
        help='The logging format to use. Default is "%%(levelname)s - %%(message)s"',
        action="store",
        dest="logging_format",
        default="%(levelname)s - %(message)s",
    )

    parser.add_argument(
        "--trace",
        help="Print the qualified name of each function as it is called. Useful if the program crashes due to an access violation and you don't know where it came from.",
        action="store_true",
        dest="trace",
    )

    parser.add_argument(
        "command",
        help="The command to run",
        nargs=OPTIONAL,
        default="amulet_editor",
        choices=valid_commands,
    )

    parser.add_argument(
        "args",
        help="The arguments to pass to the command",
        nargs=REMAINDER,
    )

    args = parser.parse_args(argv, namespace=CLIArgs())

    if valid_commands is not None and args.help:
        parser.print_help()
        sys.exit(0)

    return args
