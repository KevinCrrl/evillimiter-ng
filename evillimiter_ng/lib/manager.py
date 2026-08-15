# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import threading

import netaddr

from evillimiter_ng.console.io import IO
from evillimiter_ng.networking.host import Host
from evillimiter_ng.networking.limit import Limiter, Direction
from evillimiter_ng.networking.spoof import ARPSpoofer
from evillimiter_ng.networking.scan import HostScanner
from evillimiter_ng.networking.monitor import BandwidthMonitor
from evillimiter_ng.networking.watch import HostWatcher


class CoreLimiter:
    def __init__(self, interface: str, gateway_ip: str, gateway_mac: str, netmask):
        self.interface = interface  # specified IPv4 interface
        self.gateway_ip = gateway_ip
        self.gateway_mac = gateway_mac
        self.netmask = netmask

        # range of IP address calculated from gateway IP and netmask
        self.iprange = list(netaddr.IPNetwork(
            f"{self.gateway_ip}/{self.netmask}"))

        self.host_scanner = HostScanner(self.interface, self.iprange)
        self.arp_spoofer = ARPSpoofer(
            self.interface, self.gateway_ip, self.gateway_mac)
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
