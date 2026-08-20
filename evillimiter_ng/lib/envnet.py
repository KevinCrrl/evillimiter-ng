# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import collections
import os
import platform
import socket

import psutil
from scapy.all import ARP, Ether, conf, srp1  # pylint: disable=no-name-in-module

from evillimiter_ng.common.globals import (
    BIN_NFT,
    BIN_SYSCTL,
    BIN_TC,
    BROADCAST,
    IP_FORWARD_LOC,
)
from evillimiter_ng.console import shell
from evillimiter_ng.console.io import IO
from evillimiter_ng.lib import errors as errs
from evillimiter_ng.networking import utils as netutils

InitialArguments = collections.namedtuple(
    "InitialArguments", "interface, gateway_ip, netmask, gateway_mac"
)


def is_privileged() -> bool:
    return os.geteuid() == 0


def is_linux() -> bool:
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
            if snicaddr.family == socket.AF_INET and snicaddr.broadcast is not None:
                return interface
    raise errs.EnvnetError("The default interface could not be resolved.")


def initialize(interface: str, show_io: bool = False) -> bool:
    """
    Sets up requirements, e.g. IP-Forwarding, 3rd party applications
    """
    if not is_privileged():
        raise PermissionError("This program requires root access to found.")
    if not is_linux():
        raise errs.UnsupportedSystem(
            "This program only supports Linux \
systems."
        )
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


def get_default_netmask(interface: str) -> str:
    """
    Returns the default IPv4 netmask associated to an interface
    """
    for snicaddr in psutil.net_if_addrs()[interface]:
        if snicaddr.family == socket.AF_INET:
            return snicaddr.netmask
    raise errs.EnvnetError("The default netmask could not be resolved.")


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
    raise errs.EnvnetError(f"Mac for IP address {address} could no be resolved.")


def delete_network_settings(interface) -> bool:
    return (
        shell.execute_suppressed(
            [BIN_TC, "qdisc", "del", "dev", interface, "root", "handle", "1:0", "htb"]
        )
        == 0
        and shell.execute_suppressed([BIN_NFT, "delete", "table", "eng"]) == 0
    )


def disable_ip_forwarding() -> bool:
    return shell.execute_suppressed([BIN_SYSCTL, "-w", f"{IP_FORWARD_LOC}=0"]) == 0


def stop_eng(interface: str):
    delete_network_settings(interface)
    disable_ip_forwarding()


def process_arguments(args, show_io: bool = True) -> str | InitialArguments:
    if args.interface is None:
        try:
            interface = get_default_interface()
        except errs.EnvnetError:
            return "default interface could not be resolved. specify \
manually (-i)."
    else:
        interface = args.interface
        if not netutils.exists_interface(interface):
            return f"interface {IO.LIGHTYELLOW}{interface}\
{IO.END_LIGHTYELLOW} does not exist."

    if show_io:
        IO.ok(f"interface: {IO.LIGHTYELLOW}{interface}{IO.END_LIGHTYELLOW}")

    if args.gateway_ip is None:
        try:
            gateway_ip = get_default_gateway()
        except errs.EnvnetError:
            return "default gateway address could not be \
resolved. specify manually (-g)."
    else:
        gateway_ip = args.gateway_ip

    if show_io:
        IO.ok(f"Gateway ip: {IO.LIGHTYELLOW}{gateway_ip}{IO.END_LIGHTYELLOW}")

    if args.gateway_mac is None:
        try:
            gateway_mac = get_mac_by_ip(interface, gateway_ip)
        except errs.EnvnetError:
            return "Gateway mac address could not be resolved."
    else:
        if netutils.validate_mac_address(args.gateway_mac):
            gateway_mac = args.gateway_mac.lower()
        else:
            return "Gateway mac is invalid."

    if show_io:
        IO.ok(f"Gateway mac: {IO.LIGHTYELLOW}{gateway_mac}{IO.END_LIGHTYELLOW}")

    if args.netmask is None:
        try:
            netmask = get_default_netmask(interface)
        except errs.EnvnetError:
            return "Netmask could not be resolved. specify manually (-n)."
    else:
        netmask = args.netmask

    if show_io:
        IO.ok(f"Netmask: {IO.LIGHTYELLOW}{netmask}{IO.END_LIGHTYELLOW}")

    return InitialArguments(
        interface=interface,
        gateway_ip=gateway_ip,
        gateway_mac=gateway_mac,
        netmask=netmask,
    )
