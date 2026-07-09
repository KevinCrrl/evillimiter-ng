<p align="center"><img src="https://github.com/KevinCrrl/evillimiter-ng/blob/main/evillimiter_ng_screenshot.png?raw=true"/></p>

# Evil Limiter Next Generation

[![License Badge](https://img.shields.io/badge/license-GPLv2-blue.svg)](LICENSE)
[![Compatibility](https://img.shields.io/badge/python-3-brightgreen.svg)](PROJECT)
[![Hatch project](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pypa/hatch/master/docs/assets/badge/v0.json)](https://github.com/pypa/hatch)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/KevinCrrl/evillimiter-ng/graphs/commit-activity)
[![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=102)](https://github.com/ellerbrock/open-source-badge/)

A tool to monitor, analyze and limit the bandwidth (upload/download) of devices on your local network without physical or administrative access.

`evillimiter-ng` employs [ARP spoofing](https://en.wikipedia.org/wiki/ARP_spoofing) and [traffic shaping](https://en.wikipedia.org/wiki/Traffic_shaping) to throttle the bandwidth of hosts on the network.

## Requirements
- Linux distribution
- Python 3 or greater

Possibly missing python packages will be installed during the installation process.

## Installation


```bash
# Using Pypi and Pip

pip install evillimiter-ng

# Without Pypi and Pip

git clone https://github.com/KevinCrrl/evillimiter-ng.git
cd evillimiter-ng

## Arch-based systems (or using the AUR: https://aur.archlinux.org/packages/evillimiter-ng)
cd pkgbuild
makepkg -si

## Other GNU/Linux distros using a virtual env
python -m build # Using python3-build
hatch build # Using hatch CLI

python -m installer dist/*.whl

# or without pypi, just with pip

pip install .
```

## Quick Start Example

After installation, you can start using the tool with the following basic workflow.

1. Start the program and specify your network interface:

```bash
evillimiter-ng -i wlan0
```

2. Scan the network for connected hosts:

```bash
scan
```

3. Limit bandwidth of a device (example: device ID 3 to 200kbit):

```bash
limit 3 200kbit
```

### Example of a single-use command in the shell

```bash
# Scan the network, list hosts, block everyone for 20 seconds, and then restore connection.
echo "scan && hosts && block all && sleep 20 && free all && exit" | evillimiter-ng
```

### Exporting/Importing a JSON file to save scans

```bash
# Scan the network, and save the results in a JSON file encoded in base64
scan && export-json my_network.json
```

With it, you can restore these results without a new scan in a future session:

```bash
import-json my_network.json
```

> 🛑 **CRITICAL SECURITY WARNING**
> 
> **Base64 is NOT encryption (like PGP).** It only obfuscates sensitive data (local IPs, MAC addresses) so they aren't visible to the naked eye. **Any user or program can easily decode this file.**
> 
> * **Permissions:** The file is readable by all users, but write-protected (root only) to prevent corruption. 
> * **Risk:** Even if a malicious user obtains root access, they cannot decrypt what was never encrypted, but they *can* corrupt or destroy the information. Do not rely on this file for confidentiality.

#### Command-Line Arguments

| Argument | Explanation |
| -------- | ----------- |
| `-h` | Displays help message listing all command-line arguments |
| `-i [Interface Name]` | Specifies network interface (resolved if not specified) |
| `-g [Gateway IP Address]` | Specifies gateway IP address (resolved if not specified) |
| `-m [Gateway MAC Address]` | Specifies gateway MAC address (resolved if not specified) |
| `-n [Netmask Address]` | Specifies netmask (resolved if not specified)

#### `evillimiter-ng` Commands

| Command | Explanation |
| ------- | ----------- |
| `scan (--range [IP Range]) (--intensity [(1,2,3)])` | Scans your network for online hosts. One of the first things to do after start.<br>`--range` lets you specify a custom IP range.<br>`--intensity` lets you specify the scan intensity / speed (`1` = quick, `2` = normal (standard), `3` = intense).<br>Example: `scan --range 192.168.178.1-192.168.178.40 --intensity 1` or just `scan`. |
| `hosts` | Displays all scanned hosts and basic information. |
| `limit [ID1,ID2,...] [Rate] (--upload) (--download)` | Limits bandwidth of host(s) associated with specified ID. |
| `block [ID1,ID2,...] (--upload) (--download)` | Blocks internet connection of host(s). |
| `free [ID1,ID2,...]` | Removes bandwidth restrictions. |
| `add [IP] (--mac [MAC])` | Adds custom host manually. |
| `monitor [ID1,ID2,...] (--interval [time in ms])` | Monitor bandwidth usage of host(s). |
| `analyze [ID1,ID2,...] (--duration [time in s])` | Analyze traffic usage. |
| `watch` | Shows current watch status. |
| `watch add [ID1,ID2,...]` | Adds host(s) to watchlist. |
| `watch remove [ID1,ID2,...]` | Removes host(s) from watchlist. |
| `watch set [Attribute] [Value]` | Changes watch settings. |
| `clear` | Clears terminal window. |
| `quit` | Quits the application. |
| `sleep` | Waits for <n> seconds. |
| `?`, `help` | Displays command help. |
| `import-json, export-json [JSON_FILE_PATH]` | Import/Export a JSON file containing IP addresses and MAC addresses encoded in base64. |

## Restrictions

- **Limits IPv4 connections only**, since [ARP spoofing](https://en.wikipedia.org/wiki/ARP_spoofing) requires ARP packets which exist only in IPv4 networks.

## Legal Disclaimer

Please read the full legal disclaimer here:

[LEGAL.md](https://github.com/KevinCrrl/evillimiter-ng/blob/main/LEGAL.md)

## License

Copyright (c) 2026 by [KevinCrrl](https://github.com/KevinCrrl).

Licensed under the **GPLv2 License**.

For a detailed list of original authors, dependencies, and their respective licenses, see the [CREDITS](https://github.com/KevinCrrl/evillimiter-ng/blob/main/CREDITS.md) file.
