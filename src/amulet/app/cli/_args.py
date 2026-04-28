from argparse import Namespace


class CLIArgs(Namespace):
    help: bool
    data_dir: str | None
    config_dir: str | None
    cache_dir: str | None
    log_dir: str | None
    logging_level: int
    logging_format: str
    trace: bool
    command: str
    command_args: list[str]
