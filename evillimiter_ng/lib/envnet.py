# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import socket
import platform
import os

import psutil
from scapy.all import Ether, ARP, srp1, conf  # pylint: disable=no-name-in-module # noqa

from evillimiter_ng.networking import utils as netutils
from evillimiter_ng.console.io import IO
from evillimiter_ng.console import shell
from evillimiter_ng.lib import errors as errs
from evillimiter_ng.common.globals import (
    BIN_TC,
    BIN_NFT,
    BIN_SYSCTL,
    IP_FORWARD_LOC,
    BROADCAST,
)


def is_privileged():
    return os.geteuid() == 0


def is_linux():
    return platform.system() == "Linux"


def get_default_interface() -> str:
    """
    Returns the default IPv4 interface
    """
    interfaces = psutil.net_if_addrs()
    for interface, info in interfaces.items():
        if interface == "lo":
            continue

        for snicaddr in info:
            if snicaddr.family == socket.AF_INET and \
                    snicaddr.broadcast is not None:
                return interface
    return ""


def initialize(interface: str = get_default_interface(),
               show_io: bool = False):
    """
    Sets up requirements, e.g. IP-Forwarding, 3rd party applications
    """
    if not is_privileged():
        raise PermissionError("This program requires root access to found.")
    if not is_linux():
        raise errs.UnsupportedSystem("This program only supports Linux \
systems.")
    if not netutils.network_settings(interface):
        if show_io:
            IO.error("qdisc root handle could not be created.")
        netutils.flush_network_settings(interface)
        if show_io:
            IO.ok("Flushed network settings\n")
        if not netutils.network_settings(interface):
            if show_io:
                IO.error("""The qdisc root handle could not be created even
after the flush, your system may need to be restarted if you
updated a critical low-level component such as the kernel.""")
            return False

    if not netutils.enable_ip_forwarding():
        if show_io:
            IO.print()
            IO.error("IP forwarding could not be enabled.")
        return False

    return True


def get_default_gateway() -> str:
    """
    Returns the default IPv4 gateway address
    """
    return conf.route.route("0.0.0.0")[2]


def get_default_netmask(interface: str = get_default_interface()):
    """
    Returns the default IPv4 netmask associated to an interface
    """
    for snicaddr in psutil.net_if_addrs()[interface]:
        if snicaddr.family == socket.AF_INET:
            return snicaddr.netmask
    return None


def get_mac_by_ip(interface: str, address: str) -> str:
    """
    Resolves hardware address from IP by sending ARP request
    and receiving ARP response
    """
    # ARP packet with operation 1 (who-is) encapsulated in Ethernet frame
    # Using the BROADCAST global variable instead of hardcoded MAC
    packet = Ether(dst=BROADCAST) / ARP(op=1, pdst=address)
    response = srp1(packet, timeout=3, verbose=0, iface=interface)

    if response is not None:
        return response.hwsrc
    return ""


def delete_network_settings(interface):
    return shell.execute_suppressed(
        [BIN_TC, "qdisc", "del", "dev",
            interface, "root", "handle", "1:0", "htb"]
    ) == 0 and shell.execute_suppressed(
        [BIN_NFT, "delete", "table", "eng"]
    ) == 0


def disable_ip_forwarding():
    return shell.execute_suppressed([BIN_SYSCTL, "-w",
                                    f"{IP_FORWARD_LOC}=0"]) == 0


def stop_eng(interface: str = get_default_interface()):
    delete_network_settings(interface)
    disable_ip_forwarding()
