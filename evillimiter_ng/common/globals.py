# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

from evillimiter_ng.console import shell

BROADCAST = "ff:ff:ff:ff:ff:ff"

BIN_TC = shell.locate_bin("tc")
BIN_NFT = shell.locate_bin("nft")
BIN_SYSCTL = shell.locate_bin("sysctl")

IP_FORWARD_LOC = "net.ipv4.ip_forward"

VERSION = "3.0.0"
DESCRIPTION = "Monitors, analyzes and limits the bandwidth of devices \
on the local network (Next Generation)."
