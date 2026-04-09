"""
    Copyright (C) 2026 KevinCrrl

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; only version 2 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, see <https://www.gnu.org/licenses/>.
"""

import socket
import threading
import collections
from rich.progress import Progress, TextColumn, SpinnerColumn, BarColumn
from scapy.all import srp1, ARP, Ether  # pylint: disable=no-name-in-module
from concurrent.futures import ThreadPoolExecutor

from .host import Host
from evillimiter_ng.console.io import IO
from evillimiter_ng.common.globals import BROADCAST


class HostScanner:
    Settings = collections.namedtuple(
        "Settings", "max_workers retries timeout")

    def __init__(self, interface, iprange):
        self.interface = interface
        self.iprange = iprange

        self._quick_settings = HostScanner.Settings(
            max_workers=80, retries=0, timeout=2
        )
        self._normal_settings = HostScanner.Settings(
            max_workers=80, retries=1, timeout=3
        )
        self._intense_settings = HostScanner.Settings(
            max_workers=80, retries=5, timeout=10
        )

        self._settings = self._normal_settings
        self._settings_lock = threading.Lock()

    @property
    def settings(self):
        with self._settings_lock:
            return self._settings

    @settings.setter
    def settings(self, value):
        with self._settings_lock:
            self._settings = value

    def set_intensity(self, intensity):
        if intensity == ScanIntensity.QUICK:
            self.settings = self._quick_settings
        elif intensity == ScanIntensity.NORMAL:
            self.settings = self._normal_settings
        elif intensity == ScanIntensity.INTENSE:
            self.settings = self._intense_settings

    def scan(self, iprange=None):
        with ThreadPoolExecutor(max_workers=self.settings.max_workers) as executor:
            hosts = []
            iprange = [str(x)
                       for x in (self.iprange if iprange is None else iprange)]
            iterable = executor.map(self._sweep, iprange)

            with Progress(
                SpinnerColumn(),
                BarColumn(bar_width=None),
                TextColumn("({task.completed}/{task.total})"),
                console=IO.console,
            ) as progress:
                task = progress.add_task("Scaning...", total=len(iprange))

                try:
                    for host in iterable:
                        if host is not None:
                            try:
                                host_info = socket.gethostbyaddr(host.ip)
                                name = "" if host_info is None else host_info[0]
                                host.name = name
                            except socket.herror:
                                pass
                            hosts.append(host)
                        progress.update(task, advance=1)
                except KeyboardInterrupt:
                    IO.ok("aborted. waiting for shutdown...")

            return hosts

    def scan_for_reconnects(self, hosts, iprange=None):
        with ThreadPoolExecutor(max_workers=self.settings.max_workers) as executor:
            scanned_hosts = []
            iprange = [str(x)
                       for x in (self.iprange if iprange is None else iprange)]
            for host in executor.map(self._sweep, iprange):
                if host is not None:
                    scanned_hosts.append(host)

            reconnected_hosts = {}
            for host in hosts:
                for s_host in scanned_hosts:
                    if host.mac == s_host.mac and host.ip != s_host.ip:
                        s_host.name = host.name
                        reconnected_hosts[host] = s_host

            return reconnected_hosts

    def _sweep(self, ip):
        """
        Sends ARP packet and listens for answer,
        if present the host is online
        """
        settings = self.settings

        # Wrap ARP in Ethernet frame to resolve Scapy warnings
        # Using the BROADCAST variable as requested by the maintainer
        packet = Ether(dst=BROADCAST) / ARP(op=1, pdst=ip)
        answer = srp1(
            packet,
            iface=self.interface,
            retry=settings.retries,
            timeout=settings.timeout,
            verbose=0
        )

        if answer is not None:
            return Host(ip, answer.hwsrc, "")


class ScanIntensity:
    QUICK = 1
    NORMAL = 2
    INTENSE = 3
