import sys
import logging
import subprocess
import os
import json
import time
import re

try:
    from rich.console import Console
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

from modules.banner import banner
from modules.scanner import full_scan
from modules.scan_intensity import SCAN_INTENSITIES
from modules.dependencies import check_dependencies

ASCII_ANIM_ENABLED = True
ASCII_FRAMES = [
    "🐍    ", " 🐍   ", "  🐍  ", "   🐍 ", "    🐍", "   🐍 ", "  🐍  ", " 🐍   "
]

def ascii_loader(message, duration=2):
    if not ASCII_ANIM_ENABLED:
        print(message)
        return
    from time import sleep
    t_end = time.time() + duration
    i = 0
    while time.time() < t_end:
        frame = ASCII_FRAMES[i % len(ASCII_FRAMES)]
        sys.stdout.write(f"\r{message} {frame}")
        sys.stdout.flush()
        sleep(0.13)
        i += 1
    sys.stdout.write(f"\r{message}        \n")
    sys.stdout.flush()

def color(text, c):
    if not RICH_AVAILABLE:
        colors = {
            'cyan': '\033[1;36m', 'magenta': '\033[1;35m', 'yellow': '\033[1;33m',
            'green': '\033[1;32m', 'red': '\033[1;31m', 'reset': '\033[0m', 
            'blue': '\033[1;34m', 'bold': '\033[1m'
        }
        return f"{colors.get(c, '')}{text}{colors['reset']}"
    return f"[{c}]{text}[/{c}]"

def safe_path(path):
    return re.sub(r'[^A-Za-z0-9_\-\.\/]', '', path)

def print_banner():
    if console:
        console.print(banner() if callable(banner) else banner)
    else:
        print(banner() if callable(banner) else banner)

def print_usage():
    msg = color("[VENO]", "magenta") + " Usage: set options, show options, run, help, update, clear, exit"
    if console:
        console.print(msg)
        console.print("Type " + color("'help'", "cyan") + " for full command details.\n")
    else:
        print(msg)
        print("Type " + color("'help'", "cyan") + " for full command details.\n")

def print_help():
    lines = [
        "\n" + color("VENO Automated Recon Shell - Full Help", "magenta") + "\n",
        "  " + color("show options", "cyan"),
        "      Prints all current settings and scan parameters.",
        "  " + color("set <option> <value>", "cyan"),
        "      Set a scan option. Options include:",
        "        " + color("domain", "yellow") + "       - Target domain to scan (e.g. set domain example.com)",
        "        " + color("output", "yellow") + "       - Output directory for results (default: output)",
        "        " + color("threads", "yellow") + "      - Number of threads/tools to use (e.g. set threads 10)",
        "        " + color("wordlist", "yellow") + "     - Custom wordlist path for fuzzing/discovery",
        "        " + color("subscan", "yellow") + "      - true/false to enable/disable subdomain scan",
        "        " + color("intensity", "yellow") + "    - Scan profile (see below)",
        "      Example: set domain example.com",
        "      Example: set intensity deep",
        "      Example: set threads 50\n",
        "  " + color("run", "cyan"),
        "      Launches the full scan with the current config. Results and report will be saved to your output directory.",
        "  " + color("update", "cyan"),
        "      Updates VENO to the latest version using git and pip.",
        "  " + color("save config <filename>", "cyan"),
        "      Saves current config to a file.",
        "  " + color("load config <filename>", "cyan"),
        "      Loads config from a file.",
        "  " + color("toggle ascii", "cyan"),
        "      Enable/disable ASCII loader animation for long ops.",
        "  " + color("timer", "cyan"),
        "      Show session elapsed time.",
        "  " + color("clear", "cyan"),
        "      Clears the screen and reprints the VENO banner.",
        "  " + color("help", "cyan"),
        "      Show this help message at any time.",
        "  " + color("-h, --help", "cyan"),
        "      Show basic usage summary at any time.",
        "  " + color("exit, quit", "cyan"),
        "      Leave the shell.\n",
        color("Scan Intensities (affect wordlist, tools, threads):", "magenta") + "\n"
    ]
    for key, profile in SCAN_INTENSITIES.items():
        features = []
        if profile.get("run_nuclei_full"): features.append("extended nuclei")
        if profile.get("dalfox"): features.append("xss")
        if profile.get("xsstrike"): features.append("xsstrike")
        if profile.get("run_sqlmap"): features.append("sqlmap")
        features_str = " | ".join(features)
        lines.append(
            f"    {color(key, 'yellow')}: wordlist={os.path.basename(profile['wordlist'])}, threads={profile['threads']}" +
            (", " + features_str if features_str else ""))
    lines += [
        "\n  " + color("Example Usage:", "magenta"),
        "      set domain example.com",
        "      set intensity normal",
        "      set threads 20",
        "      run\n"
    ]
    if console:
        for line in lines:
            console.print(line)
    else:
        for line in lines:
            print(line)

def show_options(config):
    if console:
        console.print("\nCurrent VENO options:")
    else:
        print("\nCurrent VENO options:")
    for k, v in config.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                print(f"  {k}.{sk}: {sv}")
        else:
            print(f"  {k}: {v}")
    print("")
