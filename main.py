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

# Meme module (optional)
try:
    from modules.memes import get_ascii_meme, get_insult
    HAS_MEMES = True
except ImportError:
    HAS_MEMES = False

ASCII_FRAMES = [
    "🐍    ", " 🐍   ", "  🐍  ", "   🐍 ", "    🐍", "   🐍 ", "  🐍  ", " 🐍   "
]

def ascii_loader(message, duration=2):
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
    try:
        val = banner() if callable(banner) else banner
        if val is not None and str(val).strip():
            if console:
                console.print(val)
            else:
                print(val)
    except Exception:
        pass

def print_usage():
    msg = color("[VENO]", "magenta") + " Usage: set options, show options, run, help, clear, exit"
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
        "      Launches the full scan with the current config.",
        "  " + color("save config <filename>", "cyan"),
        "      Saves current config to a file.",
        "  " + color("load config <filename>", "cyan"),
        "      Loads config from a file.",
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

def merge_intensity(config, intensity):
    if intensity not in SCAN_INTENSITIES:
        msg = color(f"Unknown intensity: {intensity}. Available: {', '.join(SCAN_INTENSITIES)}", "red")
        if console:
            console.print(msg)
        else:
            print(msg)
        return
    profile = SCAN_INTENSITIES[intensity]
    config["intensity"] = intensity
    config["wordlist"] = profile["wordlist"]
    config["scan_config"]["threads"] = profile["threads"]
    for key in profile:
        if key in ("wordlist", "threads"): continue
        config["scan_config"][key] = profile[key]

def ensure_output_dirs(config):
    domain = config.get("domain")
    output_dir = config.get("output_dir", "output")
    if domain:
        path = os.path.join(output_dir, domain)
        os.makedirs(path, exist_ok=True)

def save_config(config, filename):
    try:
        filename = safe_path(filename)
        if os.path.exists(filename):
            confirm = input(color(f"[VENO] {filename} exists. Overwrite? (y/N): ", "red"))
            if confirm.strip().lower() not in ("y", "yes"):
                print(color("[VENO] Save cancelled.", "yellow"))
                return
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(color(f"[VENO] Config saved to {filename}", "green"))
    except Exception as e:
        print(color(f"[VENO] Failed to save config: {e}", "red"))

def load_config(config, filename):
    try:
        filename = safe_path(filename)
        with open(filename, 'r') as f:
            loaded = json.load(f)
            config.clear()
            config.update(loaded)
        print(color(f"[VENO] Config loaded from {filename}", "green"))
    except Exception as e:
        print(color(f"[VENO] Failed to load config: {e}", "red"))

def validate_domain(domain):
    pat = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,}$")
    return bool(pat.match(domain))

def validate_threads(threads):
    try:
        n = int(threads)
        return 1 <= n <= 1000
    except Exception:
        return False

# Command history for session logging
COMMAND_LOG = []

def main():
    session_start = time.time()
    try:
        check_dependencies()
        msg = color("🔥 [VENO] ALL DEPENDENCIES SATISFIED! 🔥", "green")
        if console:
            console.rule(msg)
        else:
            print("="*60)
            print(msg)
            print("="*60)
    except Exception as e:
        print(color(f"[VENO] Dependency check failed: {e}", "red"))
        sys.exit(3)

    print_banner()
    print_usage()

    default_intensity = "normal"
    config = {
        "domain": "",
        "output_dir": "output",
        "subscan": True,
        "intensity": default_intensity,
        "scan_config": {
            "threads": 20,
        },
        "wordlist": "",
    }

    while True:
        try:
            prompt_str = color("veno", "magenta") + color(" > ", "cyan")
            if console:
                cmd = Prompt.ask(prompt_str)
            else:
                cmd = input(prompt_str)
            cmd = cmd.strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting VENO.")
            sys.exit(0)

        if not cmd:
            continue
        COMMAND_LOG.append(cmd)

        if cmd in ("exit", "quit"):
            print("Bye.")
            break

        elif cmd == "help":
            print_help()
        elif cmd in ("-h", "--help"):
            print_usage()
        elif cmd == "show options":
            show_options(config)
        elif cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_usage()
            continue  # Immediately re-prompts after clear
        elif cmd.startswith("save config "):
            _, _, filename = cmd.partition(" ")
            filename = filename.strip().split(" ", 1)[-1]
            if filename:
                save_config(config, filename)
            else:
                print(color("[VENO] Usage: save config <filename>", "red"))
        elif cmd.startswith("load config "):
            _, _, filename = cmd.partition(" ")
            filename = filename.strip().split(" ", 1)[-1]
            if filename:
                load_config(config, filename)
            else:
                print(color("[VENO] Usage: load config <filename>", "red"))
        elif cmd == "timer":
            elapsed = time.time() - session_start
            mins, secs = divmod(int(elapsed), 60)
            print(color(f"[VENO] Session time: {mins} min {secs} sec", "yellow"))
        elif cmd.startswith("set "):
            parts = cmd.split()
            if len(parts) < 3:
                print(color("Usage: set <option> <value>", "red"))
                continue
            option = parts[1]
            value = " ".join(parts[2:])
            if option == "threads":
                if not validate_threads(value):
                    print(color("[VENO] threads must be an integer between 1 and 1000", "red"))
                    continue
                config["scan_config"]["threads"] = int(value)
            elif option == "output":
                config["output_dir"] = safe_path(value)
            elif option == "wordlist":
                if not os.path.isfile(value):
                    print(color(f"[VENO] Wordlist not found: {value}", "red"))
                    continue
                config["wordlist"] = value
            elif option == "domain":
                if not validate_domain(value):
                    print(color("[VENO] Invalid domain format.", "red"))
                    continue
                config["domain"] = value
            elif option == "subscan":
                config["subscan"] = value.lower() in ("yes", "true", "1", "on")
            elif option == "intensity":
                merge_intensity(config, value)
            else:
                print(color(f"Unknown option: {option}", "red"))
        elif cmd == "run":
            domain = config.get("domain")
            if not domain:
                print(color("Set a domain first: set domain <example.com>", "red"))
                continue
            ensure_output_dirs(config)
            try:
                log_path = os.path.join(config['output_dir'], domain, "veno.log")
                logging.basicConfig(
                    filename=log_path,
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s"
                )
                # Pre-scan meme
                if HAS_MEMES:
                    print(color(get_ascii_meme(), "yellow"))
                print(color(f"[VENO] Starting full scan for {domain} (intensity: {config['intensity']})", "magenta"))
                ascii_loader("[VENO] Starting scan...", duration=2)
                result = full_scan(domain, config)
                print(color(f"[VENO] Scan completed for {domain}", "green"))
                print(color(f"Report: {os.path.join(config['output_dir'], domain, 'report.html')}", "yellow"))
                # Print failures summary if any
                if "failures" in result and result["failures"]:
                    print(color("[VENO] Some scan steps failed:", "red"))
                    for step, err in result["failures"]:
                        print(color(f"  {step}: {err}", "red"))
                # Post-scan meme/insult
                if HAS_MEMES:
                    print(color(get_insult(), "magenta"))
                    print(color(get_ascii_meme(), "green"))
            except KeyboardInterrupt:
                print(color("[VENO] Scan interrupted by user!", "red"))
                sys.exit(1)
            except Exception as e:
                log_path = os.path.join(config['output_dir'], domain, "veno.log")
                print(color(f"[VENO] Fatal error: {e}", "red"))
                print(color(f"[VENO] See log for details: {log_path}", "yellow"))
                sys.exit(2)
        elif cmd == "history":
            print(color("[VENO] Session command history:", "cyan"))
            for h in COMMAND_LOG:
                print("  " + h)
        else:
            print(color("Unknown command. Type '-h' for usage or 'help' for full command details.", "red"))

if __name__ == "__main__":
    main()
