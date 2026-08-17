# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import socket
import threading

import netaddr

from evillimiter_ng.console.io import IO
from evillimiter_ng.lib.errors import BitError
from evillimiter_ng.networking import utils as netutils
from evillimiter_ng.networking.host import Host
from evillimiter_ng.networking.limit import Direction, Limiter
from evillimiter_ng.networking.monitor import BandwidthMonitor
from evillimiter_ng.networking.scan import HostScanner, ScanIntensity
from evillimiter_ng.networking.spoof import ARPSpoofer
from evillimiter_ng.networking.watch import HostWatcher


class CoreLimiter:
    def __init__(self, interface: str, gateway_ip: str, gateway_mac: str, netmask):
        self.interface = interface  # specified IPv4 interface
        self.gateway_ip = gateway_ip
        self.gateway_mac = gateway_mac
        self.netmask = netmask

        # range of IP address calculated from gateway IP and netmask
        self.iprange = list(netaddr.IPNetwork(f"{self.gateway_ip}/{self.netmask}"))

        self.host_scanner = HostScanner(self.interface, self.iprange)
        self.arp_spoofer = ARPSpoofer(self.interface, self.gateway_ip, self.gateway_mac)
        self.limiter = Limiter(self.interface)
        self.bandwidth_monitor = BandwidthMonitor(self.interface)
        self.host_watcher = HostWatcher(
            self.interface, self.iprange, self._reconnect_callback
        )

        # holds discovered hosts
        self.hosts: list[Host] = []
        self.hosts_lock = threading.Lock()

        # start the spoof thread
        self.arp_spoofer.start()
        # start the bandwidth monitor thread
        self.bandwidth_monitor.start()
        # start the host watch thread
        self.host_watcher.start()

    def scan(self, range: str | None = None, intensity: str = "2") -> list[Host] | None:
        if range:
            iprange = self._parse_iprange(range)
            if iprange is None:
                IO.error("invalid ip range.")
                return
        else:
            iprange = None

        if intensity:
            new_intensity = self._parse_scan_intensity(intensity)
        else:
            new_intensity = ScanIntensity.NORMAL

        self.host_scanner.set_intensity(new_intensity)

        with self.hosts_lock:
            for host in self.hosts:
                self._free_host(host)

        hosts = self.host_scanner.scan(iprange)

        self.hosts_lock.acquire()
        self.hosts = hosts
        self.hosts_lock.release()

        return hosts

    def block(
        self, id: str | int, upload: str | None = None, download: str | None = None
    ):
        hosts = self.get_hosts_by_ids(id)
        direction = self._parse_direction_args(upload, download)

        if hosts is not None and len(hosts) > 0:
            for host in hosts:
                if not host.spoofed:
                    self.arp_spoofer.add(host)

                self.limiter.block(host, direction)
                self.bandwidth_monitor.add(host)
                IO.ok(
                    f"{IO.LIGHTYELLOW}{host.ip}{IO.END_LIGHTYELLOW} \
{Direction.pretty_direction(direction)} {IO.BOLD_LIGHTRED}\
blocked{IO.END_BOLD_LIGHTRED}."
                )

    def free(self, id: str | int):
        hosts = self.get_hosts_by_ids(id)
        if hosts is not None and len(hosts) > 0:
            for host in hosts:
                self._free_host(host)

    def limit(
        self,
        id: str,
        rate: str | netutils.BitRate,
        upload: str | None = None,
        download: str | None = None,
    ):
        hosts = self.get_hosts_by_ids(id)
        if hosts is None or len(hosts) == 0:
            return

        try:
            rate = netutils.BitRate.from_rate_string(rate)
        except BitError:
            IO.error("Limit rate is invalid.")
            return

        direction = self._parse_direction_args(upload, download)

        for host in hosts:
            self.arp_spoofer.add(host)
            self.limiter.limit(host, direction, rate)
            self.bandwidth_monitor.add(host)

            IO.ok(
                f"{IO.LIGHTYELLOW}{host.ip}{IO.END_LIGHTYELLOW} \
{Direction.pretty_direction(direction)} {IO.BOLD_LIGHTRED}\
limited{IO.END_BOLD_LIGHTRED} to {rate}."
            )

    def add(self, ip: str, mac: str, name: str) -> dict[str: bool | str]:
        if not netutils.validate_ip_address(ip):
            return {"success": False, "msg": "Invalid ip address."}

        if mac:
            if not netutils.validate_mac_address(mac):
                return {"success": False, "msg": "Invalid mac address."}
        else:
            mac = netutils.get_mac_by_ip(self.interface, ip)
            if mac is None:
                return {"success": False, "msg": "Unable to resolve mac address. Specify manually (--mac)."}

        if name is None:
            try:
                host_info = socket.gethostbyaddr(ip)
                name = None if host_info is None else host_info[0]
            except socket.herror:
                pass

        host = Host(ip, mac, name)

        with self.hosts_lock:
            if host in self.hosts:
                return {"success": False, "msg": "Host does already exist."}

            self.hosts.append(host)

        return {"success": True, "msg": "Host added."}

    def interrupt_handler(self, repl: bool = False, ctrl_c: bool = False):
        if repl:
            if ctrl_c:
                IO.print()

            IO.ok("Cleaning up... stand by...")

        self.arp_spoofer.stop()
        self.bandwidth_monitor.stop()

        for host in self.hosts:
            self._free_host(host)

    def _reconnect_callback(self, old_host: Host, new_host: Host):
        """
        Callback that is called when a watched host reconnects
        Method will run in a separate thread
        """
        with self.hosts_lock:
            if old_host in self.hosts:
                self.hosts[self.hosts.index(old_host)] = new_host
            else:
                return

        self.arp_spoofer.remove(old_host, restore=False)
        self.arp_spoofer.add(new_host)

        self.host_watcher.remove(old_host)
        self.host_watcher.add(new_host)

        self.limiter.replace(old_host, new_host)
        self.bandwidth_monitor.replace(old_host, new_host)

    def _free_host(self, host: Host):
        """
        Stops ARP spoofing and unlimits host
        """
        if host.spoofed:
            self.arp_spoofer.remove(host)
            self.limiter.unlimit(host, Direction.BOTH)
            self.bandwidth_monitor.remove(host)
            self.host_watcher.remove(host)

    def _parse_direction_args(self, upload, download):
        direction = Direction.NONE

        if upload:
            direction |= Direction.OUTGOING
        if download:
            direction |= Direction.INCOMING

        return Direction.BOTH if direction == Direction.NONE else direction

    def _parse_iprange(self, ip_range):
        try:
            if "-" in ip_range:
                return list(netaddr.iter_iprange(*ip_range.split("-")))
            return list(netaddr.IPNetwork(ip_range))
        except netaddr.AddrFormatError:
            return

    def _parse_scan_intensity(self, value) -> int:
        if value.isdigit() and int(value) in (
            ScanIntensity.QUICK,
            ScanIntensity.NORMAL,
            ScanIntensity.INTENSE,
        ):
            return int(value)
        return 2

    def get_hosts_by_ids(self, ids_string: str | int) -> set[Host] | list[Host] | None:
        if isinstance(ids_string, int):
            ids_string = str(ids_string)
        if ids_string == "all":
            with self.hosts_lock:
                return self.hosts.copy()

        ids = ids_string.split(",")
        hosts = set()

        with self.hosts_lock:
            for id_ in ids:
                is_mac = netutils.validate_mac_address(id_)
                is_ip = netutils.validate_ip_address(id_)
                is_id_ = id_.isdigit()

                if not is_mac and not is_ip and not is_id_:
                    IO.error(f"Invalid identifier(s): '{ids_string}'.")
                    return

                if is_mac or is_ip:
                    found = False
                    for host in self.hosts:
                        if host.mac == id_.lower() or host.ip == id_:
                            found = True
                            hosts.add(host)
                            break
                    if not found:
                        IO.error(
                            f"No host matching {IO.LIGHTYELLOW}{id_}\
{IO.END_LIGHTYELLOW}."
                        )
                        return
                else:
                    id_ = int(id_)
                    if len(self.hosts) == 0 or id_ not in range(len(self.hosts)):
                        IO.error(
                            f"No host with id {IO.LIGHTYELLOW}{id_}\
{IO.END_LIGHTYELLOW}."
                        )
                        return
                    hosts.add(self.hosts[id_])

        return hosts
