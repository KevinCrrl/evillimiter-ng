from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from prompt_toolkit.completion import WordCompleter

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
        IO.print(f"{IO.BOLD_LIGHTGREEN }OK{IO.END_BOLD_LIGHTGREEN}   {text}", end=end)  # noqa: E202

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
        return IO.session.prompt(
            text,
            completer=WordCompleter(["scan", "hosts", "watch", "add", "limit", "block", "free",
                                    "monitor", "analyzer", "quit", "clear", "remove", "set",
                                     "--download", "--upload", "--range", "--mac",
                                     "--duration", "--intensity", "--interval", "exit", "help"]),
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
            show_frame=True
        )

    @staticmethod
    def clear():
        """
        Clears the terminal screen
        """
        shell.execute(["clear"])
