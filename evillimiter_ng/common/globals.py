# Copyright (C) 2026 KevinCrrl GPL-2.0-only

from evillimiter_ng.console import shell

BROADCAST = "ff:ff:ff:ff:ff:ff"

BIN_TC = shell.locate_bin("tc")
BIN_IPTABLES = shell.locate_bin("iptables")
BIN_SYSCTL = shell.locate_bin("sysctl")

IP_FORWARD_LOC = "net.ipv4.ip_forward"

VERSION = "2.2.0"
DESCRIPTION = "Monitors, analyzes and limits the bandwidth of devices on the local network (Next Generation)."
