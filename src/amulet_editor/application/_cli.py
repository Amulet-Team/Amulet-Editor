from argparse import ArgumentParser, Namespace
import logging
import subprocess
import sys
from collections.abc import Sequence
from amulet.app.path._application import (
    DefaultDataDir,
    DefaultConfigDir,
    DefaultCacheDir,
    DefaultLogDir,
)

from . import command as command_mod


BROKER = "BROKER"


class GlobalArgs(Namespace):
    data_dir: str | None
    config_dir: str | None
    cache_dir: str | None
    log_dir: str | None
    logging_level: int
    logging_format: str
    trace: bool


class FullArgs(GlobalArgs):
    command: str | None


def get_parser(full: bool) -> ArgumentParser:
    parser = ArgumentParser(
        prog="amulet",
        add_help=full,
        description="Amulet is a Minecraft world editing application.",
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

    if full:
        entry_subcommand = parser.add_subparsers(
            dest="command", help="The main command to run"
        )

        for command in command_mod._get_commands():
            command_parser = entry_subcommand.add_parser(
                command.name,
                *command.add_parser_args,
                **command.add_parser_kwargs,
            )
            init_argparse = command.init_argparse
            if init_argparse is not None:
                init_argparse(command_parser)

    return parser


def parse_global_args(argv: Sequence[str] | None = None) -> GlobalArgs:
    parser = get_parser(False)
    args, _ = parser.parse_known_args(argv)
    return args  # noqa


def parse_args(argv: Sequence[str] | None = None) -> FullArgs:
    parser = get_parser(True)
    args, _ = parser.parse_known_args(argv)
    return args  # noqa


# TODO: move this somewhere more sensible
def spawn_process(path: str | None = None) -> None:
    """Spawn the broker process passing over the input CLI values."""
    this_args = parse_args()
    new_args = [sys.executable, sys.argv[0]]
    # if path is not None:
    #     new_args += ["--level_path", path]
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
