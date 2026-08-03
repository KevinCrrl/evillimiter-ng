# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from rich.console import Console
from rich.table import Table

from . import shell


class IO:
    BOLD_LIGHTBLUE = "[bold bright_blue]"
    END_BOLD_LIGHTBLUE = "[/bold bright_blue]"
    BOLD_LIGHTRED = "[bold bright_red]"
    END_BOLD_LIGHTRED = "[/bold bright_red]"
    LIGHTYELLOW = "[bright_yellow]"
    END_LIGHTYELLOW = "[/bright_yellow]"
    BOLD_LIGHT = "[bright_white]"
    END_BOLD_LIGHT = "[/bright_white]"

    console = Console(emoji=False)
    session = PromptSession()

    @staticmethod
    def print(text: str | Table = "", end="\n"):
        """
        Writes a given string to the console.
        """
        IO.console.print(text, end=end)

    @staticmethod
    def ok(text, end="\n"):
        """
        Print a success status message
        """
        IO.print(f"[{IO.BOLD_LIGHTBLUE}  OK\
{IO.END_BOLD_LIGHTBLUE}  ]  {text}", end=end)  # noqa: E202

    @staticmethod
    def error(text):
        """
        Print an error status message
        """
        IO.print(f"[{IO.BOLD_LIGHTRED}ERROR!{IO.END_BOLD_LIGHTRED}]  {text}")

    @staticmethod
    def input(text):
        """
        Prompts the user for input.
        """
        try:
            return IO.session.prompt(
                text,
                completer=NestedCompleter.from_nested_dict({
                    "scan": {"-r", "-i", "--range", "--intensity"},
                    "hosts": None,
                    "limit": {"-u", "-d", "--upload", "--download"},
                    "block": {"-u", "-d", "--upload", "--download"},
                    "free": None,
                    "add": {"-m", "--mac"},
                    "monitor": {"-i", "--interval"},
                    "analyze": {"-d", "--duration"},
                    "watch": {"add", "remove", "set"},
                    "sleep": None,
                    "clear": None,
                    "exit": None,
                    "help": None,
                    "import-json": None,
                    "export-json": None
                }),
                complete_while_typing=True,
                auto_suggest=AutoSuggestFromHistory(),
                show_frame=True
            )
        except EOFError:
            return "exit"

    @staticmethod
    def clear():
        """
        Clears the terminal screen
        """
        shell.execute(["clear"])
