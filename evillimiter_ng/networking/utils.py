# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import re

from scapy.interfaces import get_if_list

from evillimiter_ng.common.globals import (
    BIN_NFT,
    BIN_SYSCTL,
    BIN_TC,
    IP_FORWARD_LOC,
)
from evillimiter_ng.console import shell
from evillimiter_ng.lib.errors import BitError, ByteValueError


def exists_interface(interface):
    """
    Determines whether or not a given interface exists
    """
    return interface in get_if_list()


def flush_network_settings(interface):
    """
    Deletes eng table using nftables
    """
    shell.execute_suppressed([BIN_NFT, "delete", "table", "eng"])

    # delete root qdisc for given interface
    shell.execute_suppressed([BIN_TC, "qdisc", "del", "dev", interface, "root"])


def validate_ip_address(ip):
    return re.match(r"^(\d{1,3}\.){3}(\d{1,3})$", ip) is not None


def validate_mac_address(mac):
    return re.match(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", mac) is not None


def network_settings(interface):
    """
    Creates a root htb qdisc in traffic control for a given interface
    """
    return (
        shell.execute_suppressed(
            [BIN_TC, "qdisc", "add", "dev", interface, "root", "handle", "1:0", "htb"]
        )
        == 0
        and shell.execute_suppressed([BIN_NFT, "add", "table", "ip", "eng"]) == 0
        and shell.execute_suppressed(
            [
                BIN_NFT,
                "add",
                "chain",
                "ip",
                "eng",
                "FORWARD",
                "{ type filter hook forward priority filter; policy accept; }",
            ]
        )
        == 0
        and shell.execute_suppressed(
            [
                BIN_NFT,
                "add",
                "chain",
                "ip",
                "eng",
                "POSTROUTING",
                "{ type filter hook postrouting priority mangle; policy accept; }",
            ]
        )
        == 0
        and shell.execute_suppressed(
            [
                BIN_NFT,
                "add",
                "chain",
                "ip",
                "eng",
                "PREROUTING",
                "{ type filter hook prerouting priority mangle; policy accept; }",
            ]
        )
        == 0
    )


def enable_ip_forwarding():
    return shell.execute_suppressed([BIN_SYSCTL, "-w", f"{IP_FORWARD_LOC}=1"]) == 0


class ValueConverter:
    @staticmethod
    def byte_to_bit(v):
        return v * 8


class BitRate:
    def __init__(self, rate=0):
        self.rate = rate

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        counter = 0
        r = self.rate

        while True:
            if r >= 1000:
                r /= 1000
                counter += 1
            else:
                unit = ""
                if counter == 0:
                    unit = "bit"
                elif counter == 1:
                    unit = "kbit"
                elif counter == 2:
                    unit = "mbit"
                elif counter == 3:
                    unit = "gbit"

                return f"{int(r)}{unit}"

            if counter > 3:
                raise BitError("Bitrate limit exceeded")

    def __mul__(self, other):
        if isinstance(other, BitRate):
            return BitRate(int(self.rate * other.rate))
        return BitRate(int(self.rate * other))

    def fmt(self, fmt):
        string = self.__str__()
        end = len([_ for _ in string if _.isdigit()])
        num = int(string[:end])

        return f"{fmt % num}{string[end:]}"

    @classmethod
    def from_rate_string(cls, rate_string):
        return cls(BitRate._bit_value(rate_string))

    @staticmethod
    def _bit_value(rate_string):
        number = 0  # rate number
        offset = 0  # string offset

        for c in rate_string:
            if c.isdigit():
                number = number * 10 + int(c)
                offset += 1
            else:
                break

        unit = rate_string[offset:].lower()

        if unit == "bit":
            return number
        if unit == "kbit":
            return number * 1000
        if unit == "mbit":
            return number * 1000**2
        if unit == "gbit":
            return number * 1000**3
        raise BitError("Invalid bitrate")


class ByteValue:
    def __init__(self, value=0):
        self.value = value

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        counter = 0
        v = self.value

        while True:
            if v >= 1024:
                v /= 1024
                counter += 1
            else:
                unit = ""
                if counter == 0:
                    unit = "b"
                elif counter == 1:
                    unit = "kb"
                elif counter == 2:
                    unit = "mb"
                elif counter == 3:
                    unit = "gb"
                elif counter == 4:
                    unit = "tb"

                return f"{int(v)}{unit}"

            if counter > 3:
                raise ByteValueError("Byte value limit exceeded")

    def __int__(self):
        return self.value

    def __add__(self, other):
        if isinstance(other, ByteValue):
            return ByteValue(int(self.value + other.value))
        return ByteValue(int(self.value + other))

    def __sub__(self, other):
        if isinstance(other, ByteValue):
            return ByteValue(int(self.value - other.value))
        return ByteValue(int(self.value - other))

    def __mul__(self, other):
        if isinstance(other, ByteValue):
            return ByteValue(int(self.value * other.value))
        return ByteValue(int(self.value * other))

    def __ge__(self, other):
        if isinstance(other, ByteValue):
            return self.value >= other.value
        return self.value >= other

    def fmt(self, fmt):
        string = self.__str__()
        end = len([_ for _ in string if _.isdigit()])
        num = int(string[:end])

        return f"{fmt % num}{string[end:]}"

    @classmethod
    def from_byte_string(cls, byte_string):
        return cls(ByteValue.byte_value(byte_string))

    @staticmethod
    def byte_value(byte_string):
        number = 0  # rate number
        offset = 0  # string offset

        for c in byte_string:
            if c.isdigit():
                number = number * 10 + int(c)
                offset += 1
            else:
                break

        unit = byte_string[offset:].lower()

        if unit == "b":
            return number
        if unit == "kb":
            return number * 1024
        if unit == "mb":
            return number * 1024**2
        if unit == "gb":
            return number * 1024**3
        if unit == "tb":
            return number * 1024**4
        raise ByteValueError("Invalid byte string")
