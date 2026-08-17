# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import base64
import binascii
import json
import os
import stat
import time
from argparse import ArgumentError, ArgumentParser, RawTextHelpFormatter
from shlex import split

from prompt_toolkit.shortcuts import yes_no_dialog
from rich.columns import Columns
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from evillimiter_ng.console.banner import MAIN_BANNER
from evillimiter_ng.console.io import IO
from evillimiter_ng.lib.manager import CoreLimiter
from evillimiter_ng.networking.host import Host
from evillimiter_ng.networking.utils import ByteValue


class MainMenu(CoreLimiter):
    def __init__(self, version, interface, gateway_ip, gateway_mac, netmask):
        super().__init__(interface, gateway_ip, gateway_mac, netmask)
        self.prompt = ">>> "
        self.parser = ArgumentParser(
            prog="",  # Empty prog because it is a REPL, not a CLI
            exit_on_error=False,
            formatter_class=RawTextHelpFormatter,
        )
        self._active = False
        self.subp = self.parser.add_subparsers()
        clear_p = self.subp.add_parser("clear", help="Clears the terminal window.")
        clear_p.set_defaults(func=self._clear_handler)

        hosts_p = self.subp.add_parser(
            "hosts",
            help="Lists all scanned hosts.\ncontains host \
information, including IDs.",
        )
        hosts_p.set_defaults(func=self._hosts_handler)

        scan_parser = self.subp.add_parser(
            "scan",
            help="scan (--range [IP range]) (--intensity [(1,2,3)])\n\
Scans for online hosts on your network.\nrequired to \
find the hosts you want to limit.\ne.g.: scan\nscan --range \
192.168.178.1-192.168.178.50\nscan --range 192.168.178.1/24 \
--intensity 3",
        )
        scan_parser.add_argument("-r", "--range")
        scan_parser.add_argument("-i", "--intensity")
        scan_parser.set_defaults(func=self._scan_handler)

        limit_parser = self.subp.add_parser(
            "limit",
            help="Limits bandwith of host(s) \
(uload/dload).\ne.g.: limit 4 100kbit\nlimit 2,3,4 1gbit \
--download\nlimit all 200kbit --upload",
        )
        limit_parser.add_argument("id")
        limit_parser.add_argument("rate")
        limit_parser.add_argument("-u", "--upload", action="store_true")
        limit_parser.add_argument("-d", "--download", action="store_true")
        limit_parser.set_defaults(func=self._limit_handler)

        block_parser = self.subp.add_parser(
            "block",
            help="Blocks internet access of \
host(s).\ne.g.: block 3,2\nblock all --upload",
        )
        block_parser.add_argument("id")
        block_parser.add_argument("-u", "--upload", action="store_true")
        block_parser.add_argument("-d", "--download", action="store_true")
        block_parser.set_defaults(func=self._block_handler)

        free_parser = self.subp.add_parser(
            "free", help="Unlimits/Unblocks host(s).\ne.g.: free 3,2\nfree all"
        )
        free_parser.add_argument("id")
        free_parser.set_defaults(func=self._free_handler)

        add_parser = self.subp.add_parser(
            "add",
            help="Adds custom host to host list.\n\
mac resolved automatically.\n\
e.g.: add 192.168.178.24\nadd 192.168.1.50 --mac \
1c:fc:bc:2d:a6:37",
        )
        add_parser.add_argument("ip")
        add_parser.add_argument("-m", "--mac")
        add_parser.add_argument("-n", "--name")
        add_parser.set_defaults(func=self._add_handler)

        import_parser = self.subp.add_parser(
            "import-json",
            help="Import a JSON file containing IP addresses \
and MAC \addresses encoded in base64.\ne.g.: import-json /root/hosts.json",
        )
        import_parser.add_argument("json_path")
        import_parser.set_defaults(func=self._import_handler)

        export_parser = self.subp.add_parser(
            "export-json",
            help="Export a JSON file containing IP addresses \
and MAC addresses encoded in base64.\ne.g.: export-json /root/hosts.json",
        )
        export_parser.add_argument("json_path")
        export_parser.set_defaults(func=self._export_handler)

        monitor_parser = self.subp.add_parser(
            "monitor",
            help="Monitors bandwidth usage of limited\
host(s).\ne.g.: monitor --with-id all --interval 600",
        )
        monitor_parser.add_argument("-w", "--with-id")
        monitor_parser.add_argument("-i", "--interval")
        monitor_parser.set_defaults(func=self._monitor_handler)

        analyze_parser = self.subp.add_parser(
            "analyze",
            help="Analyzes traffic of host(s) \
without limiting\nto determine who uses how much bandwidth.\
\ne.g.: analyze 2,3 --duration 120",
        )
        analyze_parser.add_argument("id")
        analyze_parser.add_argument("-d", "--duration")
        analyze_parser.set_defaults(func=self._analyze_handler)

        watch_parser = self.subp.add_parser(
            "watch",
            help="Detects host reconnects with different IP.\n\
Type watch --help to see the subcommands.",
        )
        watch_parser.set_defaults(func=self._watch_handler)

        watch_sub = watch_parser.add_subparsers()

        watch_add_parser = watch_sub.add_parser(
            "add",
            help="Adds host to the reconnection watchlist.\ne.g.: \
watch add 3,4",
        )
        watch_add_parser.add_argument("id")
        watch_add_parser.set_defaults(func=self._watch_add_handler)

        watch_remove_parser = watch_sub.add_parser(
            "remove",
            help="Removes host from the reconnection watchlist.\n\
e.g.: watch remove all",
        )
        watch_remove_parser.add_argument("id")
        watch_remove_parser.set_defaults(func=self._watch_remove_handler)

        watch_set_parser = watch_sub.add_parser(
            "set",
            help="Changes reconnect watch settings.\ne.g.: watch set \
interval 120\nwatch set intensity 1",
        )
        watch_set_parser.add_argument("attribute")
        watch_set_parser.add_argument("value")
        watch_set_parser.set_defaults(func=self._watch_set_handler)

        sleep_parser = self.subp.add_parser("sleep", help="Waits for <n> seconds")
        sleep_parser.add_argument("seconds")
        sleep_parser.set_defaults(func=self._sleep_handler)

        help_p = self.subp.add_parser("help", help="Shows this help.")
        help_p.set_defaults(func=self._help_handler)
        exit_p = self.subp.add_parser("exit", help="Quits the application.")
        exit_p.set_defaults(func=self._exit_handler)

        self.version = version  # application version
        self._print_help_reminder()

    def start(self):
        """
        Starts the menu input loop.
        Commands will be processed and handled.
        """
        self._active = True

        while self._active:
            try:
                command = IO.input(self.prompt)
            except KeyboardInterrupt:
                self.interrupt_handler()
                break

            # split command and parse the split subcommands by spaces
            for subcommand in command.split("&&"):
                try:
                    try:
                        args = self.parser.parse_args(split(subcommand.strip()))
                        args.func(args)
                    except ArgumentError:
                        IO.error("Invalid command.")
                        self.parser.print_help()
                    except AttributeError:
                        pass
                except SystemExit:
                    pass

    def _scan_handler(self, args):
        """
        Handles 'scan' command-line argument
        (Re)scans for hosts on the network
        """
        hosts: list[Host] = self.scan(args.range, args.intensity)
        IO.ok(
            f"{IO.LIGHTYELLOW}{len(hosts)}{IO.END_LIGHTYELLOW} \
hosts discovered."
        )
        IO.print()

    def _hosts_handler(self, args):
        """
        Handles 'hosts' command-line argument
        Displays discovered hosts
        """

        table = Table(title="Hosts")
        table.add_column(f"{IO.BOLD_LIGHT}ID{IO.END_BOLD_LIGHT}", style="yellow")
        table.add_column(f"{IO.BOLD_LIGHT}IP address{IO.END_BOLD_LIGHT}")
        table.add_column(f"{IO.BOLD_LIGHT}MAC address{IO.END_BOLD_LIGHT}")
        table.add_column(f"{IO.BOLD_LIGHT}Hostname{IO.END_BOLD_LIGHT}")
        table.add_column(f"{IO.BOLD_LIGHT}Status{IO.END_BOLD_LIGHT}")

        with self.hosts_lock:
            for host in self.hosts:
                table.add_row(
                    f"{IO.LIGHTYELLOW}{self._get_host_id(host, lock=False)}\
{IO.END_LIGHTYELLOW}",
                    host.ip,
                    host.mac,
                    host.name,
                    self.limiter.pretty_status(host),
                )

        IO.print()
        IO.print(table)
        IO.print()

    def _limit_handler(self, args):
        """
        Handles 'limit' command-line argument
        Limits bandwith of host to specified rate
        """
        self.limit(args.id, args.rate, args.upload, args.download)

    def _block_handler(self, args):
        """
        Handles 'block' command-line argument
        Blocks internet communication for host
        """
        self.block(args.id, args.upload, args.download)

    def _free_handler(self, args):
        """
        Handles 'free' command-line argument
        Frees the host from all limitations
        """
        self.free(args.id)

    def _add_handler(self, args):
        """
        Handles 'add' command-line argument
        Adds custom host to host list
        """
        add_return: dict = self.add(args.ip, args.mac, args.name)
        if not add_return["success"]:
            IO.error(add_return["msg"])
        else:
            IO.ok(add_return["msg"])

    def _monitor_handler(self, args):
        """
        Handles 'monitor' command-line argument
        Monitors hosts bandwidth usage
        """

        def get_bandwidth_results():
            with self.hosts_lock:
                return sorted(
                    [
                        x
                        for x in [
                            (y, self.bandwidth_monitor.get(y))
                            for y in self.hosts
                        ]
                        if x[1] is not None
                    ],
                    key=lambda h: not (h[0].limited or h[0].blocked),
                )

        def gen_table():
            table = Table()
            columns = [
                "ID",
                "IP address",
                "Hostname",
                "Current (per s)",
                "total",
                "Packets",
            ]
            for column in columns:
                table.add_column(column)

            host_results = get_bandwidth_results()

            for host, result in host_results:
                table.add_row(
                    str(self._get_host_id(host)),
                    host.ip,
                    host.name,
                    f"{result.upload_rate}↑ {result.download_rate}↓",
                    f"{result.upload_total_size}↑ \
                        {result.download_total_size}↓",
                    f"{result.upload_total_count}↑ \
                        {result.download_total_count}↓",
                )

            return table

        if args.with_id:
            hosts = self.get_hosts_by_ids(args.with_id)
        else:
            hosts = []

        hosts_to_be_freed = set()

        interval = 0.5  # in s
        if args.interval:
            if not args.interval.isdigit():
                IO.error("Invalid interval.")
                return

            interval = int(args.interval) / 1000  # from ms to s

        try:
            for host in hosts:
                if not host.spoofed:
                    hosts_to_be_freed.add(host)
                self.arp_spoofer.add(host)
                self.bandwidth_monitor.add(host)
        except TypeError:
            IO.error("Host not found.")

        if len(get_bandwidth_results()) == 0:
            IO.error("No hosts to be monitored.")
            return

        with Live(
            gen_table(),
            console=IO.console,
            screen=True,
            refresh_per_second=interval,
            transient=True,
        ) as live:
            while True:
                try:
                    live.update(gen_table())
                except KeyboardInterrupt:
                    live.stop()
                    break

        for host in hosts_to_be_freed:
            self._free_host(host)

    def _analyze_handler(self, args):
        hosts = self.get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            IO.error("No hosts to be analyzed.")
            return

        duration = 30  # in s
        if args.duration:
            if not args.duration.isdigit():
                IO.error("Invalid duration.")
                return

            duration = int(args.duration)

        hosts_to_be_freed = set()
        host_values = {}

        for host in hosts:
            if not host.spoofed:
                hosts_to_be_freed.add(host)

            self.arp_spoofer.add(host)
            self.bandwidth_monitor.add(host)

            host_result = self.bandwidth_monitor.get(host)
            host_values[host] = {}
            host_values[host]["prev"] = (
                host_result.upload_total_size,
                host_result.download_total_size,
            )

        IO.ok(f"Analyzing traffic for {duration}s.")
        time.sleep(duration)

        error_occurred = False
        for host in hosts:
            host_result = self.bandwidth_monitor.get(host)

            if host_result is None:
                # host reconnected during analysis
                IO.error("Host reconnected during analysis.")
                error_occurred = True
            else:
                host_values[host]["current"] = (
                    host_result.upload_total_size,
                    host_result.download_total_size,
                )

        IO.ok("Cleaning up...")
        for host in hosts_to_be_freed:
            self._free_host(host)

        if error_occurred:
            return

        up_bytes = []
        down_bytes = []

        up_panel = Table(title="Upload")
        up_panel.add_column("Id")
        up_panel.add_column("Ip")
        up_panel.add_column("Hostname")
        up_panel.add_column("Upload Bar")
        down_panel = Table(title="Download")
        down_panel.add_column("Id")
        down_panel.add_column("Ip")
        down_panel.add_column("Hostname")
        down_panel.add_column("Download Bar")

        def get_values(host) -> dict:
            upload_value = (
                host_values[host]["current"][0] - host_values[host]["prev"][0]
            )
            download_value = (
                host_values[host]["current"][1] - host_values[host]["prev"][1]
            )
            return {"up": upload_value, "down": download_value}

        for host in hosts:
            values = get_values(host)
            up_bytes.append(ByteValue.byte_value(values["up"].__str__()))
            down_bytes.append(ByteValue.byte_value(values["down"].__str__()))

        max_up = max(up_bytes)
        max_down = max(down_bytes)

        for host in hosts:
            values = get_values(host)
            up_progress = Progress(
                BarColumn(), TextColumn(str(values["up"])), console=IO.console
            )
            down_progress = Progress(
                BarColumn(), TextColumn(str(values["down"])), console=IO.console
            )
            up_task = up_progress.add_task(description=":", total=max_up)
            down_task = down_progress.add_task(description=":", total=max_down)
            up_progress.update(up_task, advance=int(values["up"]))
            down_progress.update(down_task, advance=int(values["down"]))
            hid = str(self._get_host_id(host))
            ip = host.ip
            name = host.name
            up_panel.add_row(hid, ip, name, up_progress.get_renderable())
            down_panel.add_row(hid, ip, name, down_progress.get_renderable())

        IO.console.print(Columns([up_panel, down_panel]))

    def _watch_handler(self, args):
        if len(args.__dict__) == 1:
            watch_table_data = [
                f"{IO.BOLD_LIGHT}ID{IO.END_BOLD_LIGHT}",
                f"{IO.BOLD_LIGHT}IP address{IO.END_BOLD_LIGHT}",
                f"{IO.BOLD_LIGHT}MAC address{IO.END_BOLD_LIGHT}",
            ]

            set_table_data = [
                f"{IO.BOLD_LIGHT}Attribute{IO.END_BOLD_LIGHT}",
                f"{IO.BOLD_LIGHT}Value{IO.END_BOLD_LIGHT}",
            ]

            hist_table_data = [
                f"{IO.BOLD_LIGHT}ID{IO.END_BOLD_LIGHT}",
                f"{IO.BOLD_LIGHT}Old IP address{IO.END_BOLD_LIGHT}",
                f"{IO.BOLD_LIGHT}New IP address{IO.END_BOLD_LIGHT}",
                f"{IO.BOLD_LIGHT}Time{IO.END_BOLD_LIGHT}",
            ]

            watch_table = Table(title="Watchlist")
            for data in watch_table_data:
                watch_table.add_column(data)
            set_table = Table(title="Setting")
            for data in set_table_data:
                set_table.add_column(data)
            hist_table = Table(title="Reconnection History")
            for data in hist_table_data:
                hist_table.add_column(data)

            iprange = self.host_watcher.iprange
            interval = self.host_watcher.interval
            intensity = self.host_watcher.intensity

            set_table.add_row(
                f"{IO.LIGHTYELLOW}range{IO.END_LIGHTYELLOW}",
                f"{len(iprange)} addresses" if iprange is not None else "default",
            )

            set_table.add_row(
                f"{IO.LIGHTYELLOW}interval{IO.END_LIGHTYELLOW}", f"{interval}s"
            )

            set_table.add_row(
                f"{IO.LIGHTYELLOW}intensity{IO.END_LIGHTYELLOW}", str(intensity)
            )

            for host in self.host_watcher.hosts:
                watch_table.add_row(
                    f"{IO.LIGHTYELLOW}{self._get_host_id(host)}\
                        {IO.END_LIGHTYELLOW}",
                    host.ip,
                    host.mac,
                )

            for recon in self.host_watcher.log_list:
                hist_table.add_row(
                    recon["old"].mac, recon["old"].ip, recon["new"].ip, recon["time"]
                )

            IO.print()
            IO.print(watch_table)
            IO.print()
            IO.print(set_table)
            IO.print()
            IO.print(hist_table)
            IO.print()

    def _watch_add_handler(self, args):
        """
        Handles 'watch add' command-line argument
        Adds host to the reconnection watch list
        """
        hosts = self.get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return

        for host in hosts:
            self.host_watcher.add(host)

    def _watch_remove_handler(self, args):
        """
        Handles 'watch remove' command-line argument
        Removes host from the reconnection watch list
        """
        hosts = self.get_hosts_by_ids(args.id)
        if hosts is None or len(hosts) == 0:
            return

        for host in hosts:
            self.host_watcher.remove(host)

    def _watch_set_handler(self, args):
        """
        Handles 'watch set' command-line argument
        Modifies settings of the reconnection watcher
        """
        if args.attribute.lower() in ("range", "iprange", "ip_range"):
            iprange = self._parse_iprange(args.value)
            if iprange is not None:
                self.host_watcher.iprange = iprange
            else:
                IO.error("Invalid IP range.")
        elif args.attribute.lower() in ("interval"):
            if args.value.isdigit():
                self.host_watcher.interval = int(args.value)
            else:
                IO.error("Invalid interval.")
        elif args.attribute.lower() in ("intensity", "scan_intensity"):
            intensity = self._parse_scan_intensity(args.value)
            if intensity is not None:
                self.host_watcher.intensity = intensity
            else:
                IO.error("Invalid scan intensity level.")
        else:
            IO.error(
                f"{IO.LIGHTYELLOW}{args.attribute}{IO.END_LIGHTYELLOW} is \
an invalid settings attribute."
            )

    def _sleep_handler(self, args):
        try:
            time.sleep(float(args.seconds))
        except ValueError:
            IO.error("Seconds must be an int or float")

    def _export_handler(self, args):
        write: bool = True
        if os.path.exists(args.json_path):
            write = yes_no_dialog(
                "There is already a file with that path and name.",
                "Want to overwrite the file?",
            ).run()

        if write:
            info: dict = {}
            for host in self.hosts:
                info[host.ip] = {"mac": host.mac, "hostname": host.name}
            try:
                # Read and Write for owner (root)
                fd: int = os.open(
                    args.json_path,
                    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    stat.S_IRUSR | stat.S_IWUSR,
                )

                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(base64.b64encode(str(info).encode()).decode())
            except (FileNotFoundError, IsADirectoryError) as e:
                IO.error(e)

    def _import_handler(self, args):
        try:
            with open(args.json_path, "r", encoding="utf-8") as f:
                try:
                    json_dict = json.loads(
                        base64.b64decode(f.read(), validate=True)
                        .decode()
                        .replace("'", '"')
                    )
                except binascii.Error:
                    IO.error(
                        "The Base64 encoding of the JSON appears to \
be corrupted."
                    )
                else:
                    for ip_arg, sub_dict in json_dict.items():
                        IO.print(f"Adding host {ip_arg}")
                        try:
                            sub_dict["hostname"]
                        except KeyError:
                            sub_dict["hostname"] = None
                        self._add_handler(
                            Host(ip_arg, sub_dict["mac"], sub_dict["hostname"])
                        )
        except (FileNotFoundError, IsADirectoryError) as e:
            IO.error(e)

    def _clear_handler(self, args):
        """
        Handler for the 'clear' command-line argument
        Clears the terminal window and re-prints the banner
        """
        IO.clear()
        IO.print(MAIN_BANNER)
        self._print_help_reminder()

    def _help_handler(self, args):
        """
        Handles 'help' command-line argument
        Prints help message including commands and usage
        """
        self.parser.print_help()

    def _exit_handler(self, args):
        self.interrupt_handler(repl=True)
        self._active = False

    def _get_host_id(self, host, lock=True):
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

    def _print_help_reminder(self):
        IO.print(
            f"Type {IO.LIGHTYELLOW}help{IO.END_LIGHTYELLOW} or \
{IO.LIGHTYELLOW}-h{IO.END_LIGHTYELLOW} to show command \
information."
        )
