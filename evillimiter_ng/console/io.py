from rich.console import Console

from . import shell


class IO():
    BOLD_LIGHTGREEN = "[bold bright_green]"
    END_BOLD_LIGHTGREEN = "[/bold bright_green]"
    BOLD_LIGHTRED = "[bold bright_red]"
    END_BOLD_LIGHTRED = "[/bold bright_red]"
    LIGHTYELLOW = "[bright_yellow]"
    END_LIGHTYELLOW = "[/bright_yellow]"
    BOLD_LIGHT = "[bright_white]"
    END_BOLD_LIGHT = "[/bright_white]"

    console = Console(emoji=False)

    @staticmethod
    def print(text, end='\n'):
        """
        Writes a given string to the console.
        """
        IO.console.print(text, end=end, emoji=False)

    @staticmethod
    def ok(text, end='\n'):
        """
        Print a success status message
        """
        IO.print(f'{IO.BOLD_LIGHTGREEN }OK{IO.END_BOLD_LIGHTGREEN}   {text}', end=end)

    @staticmethod
    def error(text):
        """
        Print an error status message
        """
        IO.print(f'{IO.BOLD_LIGHTRED}ERR{IO.END_BOLD_LIGHTRED}  {text}')

    @staticmethod
    def spacer():
        """
        Prints a blank line for attraction purposes
        """
        IO.print('')

    @staticmethod
    def input(prompt):
        """
        Prompts the user for input.
        """
        IO.print(prompt, "")
        return input()

    @staticmethod
    def clear():
        """
        Clears the terminal screen
        """
        shell.execute(['clear'])
