# Copyright (C) 2026 KevinCrrl and Evillimiter-NG Contributors
# SPDX-License-Identifier: GPL-2.0-only

import subprocess
from shutil import which

from evillimiter_ng.console.io import IO


def execute(command):
    return subprocess.run(command, check=False).returncode


def execute_suppressed(command):
    return subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
    ).returncode


def execute_output(command):
    return subprocess.run(command, check=False, capture_output=True, text=True).stdout


def locate_bin(name):
    search_bin = which(name)
    return (
        search_bin
        if search_bin is not None
        else IO.error(
            f"missing util: \
{name}, check your PATH"
        )
    )
