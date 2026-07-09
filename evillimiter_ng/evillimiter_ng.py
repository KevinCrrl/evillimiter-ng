# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import os
import sys
import argparse
import platform
import collections

import evillimiter_ng.networking.utils as netutils
from evillimiter_ng.menus.main_menu import MainMenu
from evillimiter_ng.console.banner import MAIN_BANNER
from evillimiter_ng.console.io import IO
from evillimiter_ng.common import globals as gb

InitialArguments = collections.namedtuple(
    "InitialArguments", "interface, gateway_ip, netmask, gateway_mac"
)


def is_privileged():
    return os.geteuid() == 0


def is_linux():
    return platform.system() == "Linux"


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
        help="Displays the version of the program currently in use."
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
{IO.BOLD_LIGHTBLUE}{gb.VERSION}{IO.END_BOLD_LIGHTBLUE}")
        sys.exit(0)

    if args.interface is None:
        interface = netutils.get_default_interface()
        if interface is None:
            IO.error(
                "default interface could not be resolved. specify \
manually (-i).")
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
        gateway_ip = netutils.get_default_gateway()
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
        gateway_mac = netutils.get_mac_by_ip(interface, gateway_ip)
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
        netmask = netutils.get_default_netmask(interface)
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


def initialize(interface):
    """
    Sets up requirements, e.g. IP-Forwarding, 3rd party applications
    """
    if not netutils.create_qdisc_root(interface):
        IO.print()
        IO.error("qdisc root handle could not be created.")
        netutils.flush_network_settings(interface)
        IO.ok("Flushed network settings\n")
        if not netutils.create_qdisc_root(interface):
            IO.error("""The qdisc root handle could not be created even after the flush,
your system may need to be restarted if you updated a critical
low-level component such as the kernel.""")
            return False

    if not netutils.enable_ip_forwarding():
        IO.print()
        IO.error("IP forwarding could not be enabled.")
        return False

    return True


def cleanup(interface):
    """
    Resets what has been initialized
    """
    netutils.delete_qdisc_root(interface)
    netutils.disable_ip_forwarding()


def main():
    """
    Main entry point of the application
    """
    if not is_linux():
        IO.error("Run under linux.")
        return

    if not is_privileged():
        IO.error("Run as root.")
        return

    args = parse_arguments()

    args = process_arguments(args)

    IO.print(MAIN_BANNER)

    if args is None:
        return

    if initialize(args.interface):
        menu = MainMenu(
            gb.VERSION, args.interface, args.gateway_ip,
            args.gateway_mac, args.netmask
        )
        menu.start()
        cleanup(args.interface)
