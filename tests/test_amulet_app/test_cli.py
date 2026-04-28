import unittest
import logging

from amulet.app.cli._parser import parse_cli
from amulet.app.cli._args import CLIArgs


class CLITestCase(unittest.TestCase):
    def _check_args(
        self,
        cli_args: CLIArgs,
        *,
        data_dir: str | None = None,
        config_dir: str | None = None,
        cache_dir: str | None = None,
        log_dir: str | None = None,
        logging_level: int = logging.INFO,
        logging_format: str = "%(levelname)s - %(message)s",
        trace: bool = False,
        command: str = "amulet_launcher",
        args: list[str] | None = None,
    ):
        if data_dir is None:
            self.assertIsNone(cli_args.data_dir)
        else:
            self.assertEqual(data_dir, cli_args.data_dir)
        if config_dir is None:
            self.assertIsNone(cli_args.config_dir)
        else:
            self.assertEqual(config_dir, cli_args.config_dir)
        if cache_dir is None:
            self.assertIsNone(cli_args.cache_dir)
        else:
            self.assertEqual(cache_dir, cli_args.cache_dir)
        if log_dir is None:
            self.assertIsNone(cli_args.log_dir)
        else:
            self.assertEqual(log_dir, cli_args.log_dir)
        self.assertEqual(logging_level, cli_args.logging_level)
        self.assertEqual(logging_format, cli_args.logging_format)
        self.assertEqual(trace, cli_args.trace)
        self.assertEqual(command, cli_args.command)
        self.assertEqual(args or [], cli_args.args)

    def test_cli_default(self) -> None:
        cli_args = parse_cli()
        self.assertIsInstance(cli_args, CLIArgs)
        self._check_args(cli_args)

    def test_cli_empty(self) -> None:
        cli_args = parse_cli([])
        self.assertIsInstance(cli_args, CLIArgs)
        self._check_args(cli_args)

    def test_cli_args(self) -> None:
        cli_args = parse_cli(
            [
                "--data_dir",
                "a",
                "--config_dir",
                "b",
                "--cache_dir",
                "c",
                "--log_dir",
                "d",
                "--logging_level",
                "1",
                "--logging_format",
                "e",
                "--trace",
            ]
        )
        self.assertIsInstance(cli_args, CLIArgs)
        self._check_args(
            cli_args,
            data_dir="a",
            config_dir="b",
            cache_dir="c",
            log_dir="d",
            logging_level=1,
            logging_format="e",
            trace=True,
        )

    def test_cli_command(self) -> None:
        cli_args = parse_cli(["command", "arg"])
        self.assertIsInstance(cli_args, CLIArgs)
        self._check_args(cli_args, command="command", args=["arg"])

    def test_cli_full(self) -> None:
        cli_args = parse_cli(
            [
                "--data_dir",
                "a",
                "--config_dir",
                "b",
                "--cache_dir",
                "c",
                "--log_dir",
                "d",
                "--logging_level",
                "1",
                "--logging_format",
                "e",
                "--trace",
                "command",
                "--data_dir",
                "",
                "--config_dir",
                "",
                "--cache_dir",
                "",
                "--log_dir",
                "",
                "--logging_level",
                "0",
                "--logging_format",
                "",
                "--trace",
            ]
        )
        self.assertIsInstance(cli_args, CLIArgs)
        self._check_args(
            cli_args,
            data_dir="a",
            config_dir="b",
            cache_dir="c",
            log_dir="d",
            logging_level=1,
            logging_format="e",
            trace=True,
            command="command",
            args=[
                "--data_dir",
                "",
                "--config_dir",
                "",
                "--cache_dir",
                "",
                "--log_dir",
                "",
                "--logging_level",
                "0",
                "--logging_format",
                "",
                "--trace",
            ],
        )

    def test_invalid_arg(self) -> None:
        with self.assertRaises(SystemExit):
            parse_cli(["--testinvalidarg"])

    def test_help(self) -> None:
        parse_cli(["-h"])
        parse_cli(["--help"])
        with self.assertRaises(SystemExit):
            parse_cli(["-h"], ["amulet_launcher", "a", "b", "c"])
        with self.assertRaises(SystemExit):
            parse_cli(["--help"], ["amulet_launcher", "a", "b", "c"])

    def test_invalid_command(self) -> None:
        with self.assertRaises(SystemExit):
            parse_cli(["command"], ["amulet_launcher", "a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
