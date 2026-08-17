# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import base64
import binascii
import json
import os
import socket
import stat
import threading
from pathlib import Path

import netaddr
from prompt_toolkit.shortcuts import yes_no_dialog

from evillimiter_ng.console.io import IO
from evillimiter_ng.lib.envnet import get_mac_by_ip
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

    def add(self, ip: str, mac: str, name: str) -> dict[str, bool | str]:
        if not netutils.validate_ip_address(ip):
            return {"success": False, "msg": "Invalid ip address."}

        if mac:
            if not netutils.validate_mac_address(mac):
                return {"success": False, "msg": "Invalid mac address."}
        else:
            mac = get_mac_by_ip(self.interface, ip)
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

    def export_json(self, json_path: str | Path) -> dict[str, bool | str | None]:
        write: bool = True
        if os.path.exists(json_path):
            write = yes_no_dialog(
                "There is already a file with that path and name.",
                "Want to overwrite the file?",
            ).run()

        if write:
            info: dict = {}
            for host in self.hosts:
                if host.name is None:
                    host.name = ""
                info[host.ip] = {"mac": host.mac, "hostname": host.name}
            try:
                # Read and Write for owner (root)
                fd: int = os.open(
                    json_path,
                    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    stat.S_IRUSR | stat.S_IWUSR,
                )

                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(base64.b64encode(str(info).encode()).decode())
                    return {"success": True, "msg": None}
            except (FileNotFoundError, IsADirectoryError) as e:
                return {"success": False, "msg": str(e)}
        else:
            return {"success": False, "msg": "The file could not be written."}

    def import_json(self, json_path: str | Path) -> dict[str, bool | str | None]:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                try:
                    json_dict = json.loads(
                        base64.b64decode(f.read(), validate=True)
                        .decode()
                        .replace("'", '"')
                    )
                except binascii.Error:
                    return {"success": False, "msg": "The Base64 encoding of the JSON appears to be corrupted."}
                else:
                    for ip_arg, sub_dict in json_dict.items():
                        IO.print(f"Adding host {ip_arg}")
                        try:
                            sub_dict["hostname"]
                        except KeyError:
                            sub_dict["hostname"] = None
                        add_dict = self.add(ip_arg, sub_dict["mac"], sub_dict["hostname"])
                        if add_dict["success"]:
                            IO.ok(add_dict["msg"])
                        else:
                            IO.error(add_dict["msg"])
                    return {"success": True, "msg": None}
        except (FileNotFoundError, IsADirectoryError) as e:
            return {"success": False, "msg": str(e)}

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

    def get_host_id(self, host: Host, lock: bool = True):
        ret = None

        if lock:
            self.hosts_lock.acquire()

        for i, host_ in enumerate(self.hosts):
            if host_ == host:
                ret = i
                break

        if lock:
            self.hosts_lock.release()

        return ret
