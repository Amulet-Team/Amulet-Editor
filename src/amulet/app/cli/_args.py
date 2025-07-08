from argparse import Namespace


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
