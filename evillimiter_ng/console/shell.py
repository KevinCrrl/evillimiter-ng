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
