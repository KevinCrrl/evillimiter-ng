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

import os
import subprocess
from evillimiter_ng.console.io import IO

DEVNULL = open(os.devnull, "w")


def execute(command):
    return subprocess.run(command, check=False).returncode


def execute_suppressed(command):
    return subprocess.run(
        command, stdout=DEVNULL, stderr=DEVNULL, check=False
    ).returncode


def output(command):
    return subprocess.run(command, capture_output=True, text=True, check=False).stdout


def output_suppressed(command: list):
    return subprocess.run(command, capture_output=True, text=True, check=False).stdout


def locate_bin(name):
    try:
        return output_suppressed(["which", name]).replace("\n", "")
    except subprocess.CalledProcessError:
        IO.error(f"missing util: {name}, check your PATH")
