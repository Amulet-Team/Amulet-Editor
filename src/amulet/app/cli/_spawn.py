import sys
import subprocess

from ._parser import parse_global_args


def spawn_process(command: str, *args: str) -> None:
    """Spawn a new process with the specificed command and arguments."""
    global_args = parse_global_args()
    new_args = [
        sys.executable,
        sys.argv[0],
        "--logging_level",
        str(global_args.logging_level),
        "--logging_format",
        global_args.logging_format,
    ]
    if global_args.trace:
        new_args.append("--trace")
    if global_args.data_dir:
        new_args.extend(["--data_dir", global_args.data_dir])
    if global_args.config_dir:
        new_args.extend(["--config_dir", global_args.config_dir])
    if global_args.cache_dir:
        new_args.extend(["--cache_dir", global_args.cache_dir])
    if global_args.log_dir:
        new_args.extend(["--log_dir", global_args.log_dir])

    new_args.extend([command, *args])

    subprocess.Popen(
        new_args,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
