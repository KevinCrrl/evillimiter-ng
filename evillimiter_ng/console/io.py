"""
    Copyright (C) 2026 KevinCrrl

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; only version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, see <https://www.gnu.org/licenses/>.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from rich.console import Console

from . import shell


class IO:
    BOLD_LIGHTGREEN = "[bold bright_green]"
    END_BOLD_LIGHTGREEN = "[/bold bright_green]"
    BOLD_LIGHTRED = "[bold bright_red]"
    END_BOLD_LIGHTRED = "[/bold bright_red]"
    LIGHTYELLOW = "[bright_yellow]"
    END_LIGHTYELLOW = "[/bright_yellow]"
    BOLD_LIGHT = "[bright_white]"
    END_BOLD_LIGHT = "[/bright_white]"

    console = Console(emoji=False)
    session = PromptSession()

    @staticmethod
    def print(text, end="\n"):
        """
        Writes a given string to the console.
        """
        IO.console.print(text, end=end, emoji=False)

    @staticmethod
    def ok(text, end="\n"):
        """
        Print a success status message
        """
        IO.print(f"{IO.BOLD_LIGHTGREEN}OK{IO.END_BOLD_LIGHTGREEN}   {text}", end=end)  # noqa: E202

    @staticmethod
    def error(text):
        """
        Print an error status message
        """
        IO.print(f"{IO.BOLD_LIGHTRED}ERR{IO.END_BOLD_LIGHTRED}  {text}")

    @staticmethod
    def spacer():
        """
        Prints a blank line for attraction purposes
        """
        IO.print("")

    @staticmethod
    def input(text):
        """
        Prompts the user for input.
        """
        try:
            return IO.session.prompt(
                text,
                completer=NestedCompleter.from_nested_dict({
                    "scan": {"--range", "--intensity"},
                    "hosts": None,
                    "limit": {"--upload", "--download"},
                    "block": {"--upload", "--download"},
                    "free": None,
                    "add": {"--mac"},
                    "monitor": {"--interval"},
                    "analyze": {"--duration"},
                    "watch": {"add", "remove", "set"},
                    "sleep": None,
                    "clear": None,
                    "quit": None,
                    "exit": None,
                    "help": None
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
