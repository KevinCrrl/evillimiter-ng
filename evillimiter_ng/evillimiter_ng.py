# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import argparse
import sys

from evillimiter_ng.common import globals as gb
from evillimiter_ng.console.banner import MAIN_BANNER
from evillimiter_ng.console.io import IO
from evillimiter_ng.lib import envnet
from evillimiter_ng.lib.envnet import initialize
from evillimiter_ng.lib.errors import EnvnetError, UnsupportedSystem
from evillimiter_ng.menus.main_menu import MainMenu


def parse_arguments():
    """
    Parses the main command-line arguments (sys.argv)
    using argparse
    """
    parser = argparse.ArgumentParser(description=gb.DESCRIPTION)
    parser.add_argument(
        "-i",
        "--interface",
        help="Network interface connected to the target network. \
automatically resolved if not specified.",
    )
    parser.add_argument(
        "-g",
        "--gateway-ip",
        dest="gateway_ip",
        help="Default gateway ip address. automatically resolved \
if not specified.",
    )
    parser.add_argument(
        "-m",
        "--gateway-mac",
        dest="gateway_mac",
        help="Gateway mac address. automatically resolved if not specified.",
    )
    parser.add_argument(
        "-n",
        "--netmask",
        help="Netmask for the network. automatically resolved if \
not specified.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Displays the version of the program currently in use.",
    )
    parser.add_argument(
        "-s",
        "--shh",
        action="store_true",
        help="Enables a shell mode for typing commands and hides banners and flashy elements."
    )

    return parser.parse_args()


def main():
    """
    Main entry point of the application
    """
    try:
        args = parse_arguments()
        shh = args.shh

        if args.version:
            IO.print(
                f"EvilLimiter Next Generation Version \
{IO.BOLD_LIGHTBLUE}{gb.VERSION}{IO.END_BOLD_LIGHTBLUE}"
            )
            sys.exit(0)

        args = envnet.process_arguments(args, not shh)

        if isinstance(args, str):
            IO.error(args)
            sys.exit(1)

        if not shh:
            IO.print(MAIN_BANNER)

        try:
            if initialize(args.interface, not shh):
                menu = MainMenu(
                    gb.VERSION,
                    args.interface,
                    args.gateway_ip,
                    args.gateway_mac,
                    args.netmask,
                    True,
                    sh_mode=shh
                )
        except EnvnetError as e:
            IO.error(e)
            sys.exit(1)
        menu.start()
        envnet.stop_eng(args.interface)
    except PermissionError:
        IO.error("Run as root.")
    except UnsupportedSystem:
        IO.error("Run under Linux")
