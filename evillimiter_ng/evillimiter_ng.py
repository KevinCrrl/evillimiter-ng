# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import argparse
import collections
import sys

import evillimiter_ng.networking.utils as netutils
from evillimiter_ng.common import globals as gb
from evillimiter_ng.console.banner import MAIN_BANNER
from evillimiter_ng.console.io import IO
from evillimiter_ng.lib import envnet
from evillimiter_ng.lib.envnet import initialize
from evillimiter_ng.lib.errors import UnsupportedSystem
from evillimiter_ng.menus.main_menu import MainMenu

InitialArguments = collections.namedtuple(
    "InitialArguments", "interface, gateway_ip, netmask, gateway_mac"
)


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

    return parser.parse_args()


def process_arguments(args):
    """
    Processes the specified command-line arguments, adds them to a named tuple
    and returns.
    Executes actions specified in the command line, e.g. flush network settings
    """
    if args.version:
        IO.print(
            f"EvilLimiter Next Generation Version \
{IO.BOLD_LIGHTBLUE}{gb.VERSION}{IO.END_BOLD_LIGHTBLUE}"
        )
        sys.exit(0)

    if args.interface is None:
        interface = envnet.get_default_interface()
        if interface is None:
            IO.error(
                "default interface could not be resolved. specify \
manually (-i)."
            )
            return
    else:
        interface = args.interface
        if not netutils.exists_interface(interface):
            IO.error(
                f"interface {IO.LIGHTYELLOW}{interface}\
{IO.END_LIGHTYELLOW} does not exist."
            )
            return

    IO.ok(f"interface: {IO.LIGHTYELLOW}{interface}{IO.END_LIGHTYELLOW}")

    if args.gateway_ip is None:
        gateway_ip = envnet.get_default_gateway()
        if gateway_ip is None:
            IO.error(
                "default gateway address could not be \
resolved. specify manually (-g)."
            )
            return
    else:
        gateway_ip = args.gateway_ip

    IO.ok(f"Gateway ip: {IO.LIGHTYELLOW}{gateway_ip}{IO.END_LIGHTYELLOW}")

    if args.gateway_mac is None:
        gateway_mac = envnet.get_mac_by_ip(interface, gateway_ip)
        if gateway_mac is None:
            IO.error("Gateway mac address could not be resolved.")
            return
    else:
        if netutils.validate_mac_address(args.gateway_mac):
            gateway_mac = args.gateway_mac.lower()
        else:
            IO.error("Gateway mac is invalid.")
            return

    IO.ok(f"Gateway mac: {IO.LIGHTYELLOW}{gateway_mac}{IO.END_LIGHTYELLOW}")

    if args.netmask is None:
        netmask = envnet.get_default_netmask(interface)
        if netmask is None:
            IO.error("Netmask could not be resolved. specify manually (-n).")
            return
    else:
        netmask = args.netmask

    IO.ok(f"Netmask: {IO.LIGHTYELLOW}{netmask}{IO.END_LIGHTYELLOW}")

    return InitialArguments(
        interface=interface,
        gateway_ip=gateway_ip,
        gateway_mac=gateway_mac,
        netmask=netmask,
    )


def main():
    """
    Main entry point of the application
    """
    try:
        args = parse_arguments()

        args = process_arguments(args)

        IO.print(MAIN_BANNER)

        if args is None:
            return

        if initialize(args.interface, True):
            menu = MainMenu(
                gb.VERSION,
                args.interface,
                args.gateway_ip,
                args.gateway_mac,
                args.netmask,
            )
            menu.start()
            envnet.stop_eng(args.interface)
    except PermissionError:
        IO.error("Run as root.")
    except UnsupportedSystem:
        IO.error("Run under Linux")
