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

# Module imports with error handling
try:
    from modules.banner import banner
except Exception as e:
    banner = lambda: f"[!] Failed to load banner module: {e}"

try:
    from modules.scanner import full_scan
except Exception as e:
    def full_scan(*args, **kwargs):
        print(f"[!] Scanner module not available: {e}")

try:
    from modules.scan_intensity import SCAN_INTENSITIES
except Exception as e:
    SCAN_INTENSITIES = {}
    print(f"[!] scan_intensity module error: {e}")

try:
    from modules.dependencies import check_dependencies
except Exception as e:
    def check_dependencies():
        print(f"[!] dependencies module not available: {e}")

# Meme module (optional)
try:
    from modules.memes import get_ascii_meme, get_insult
    HAS_MEMES = True
except ImportError:
    HAS_MEMES = False
    get_ascii_meme = lambda: "¯\\_(ツ)_/¯"
    get_insult = lambda: "No memes for you!"

# CYBERPUNK COLOR PALETTE (ANSI/Rich)
COLOR_PALETTE = {
    "accent": "magenta",
    "primary": "cyan",
    "success": "green",
    "warn": "yellow",
    "fail": "red",
    "info": "blue",
    "white": "white",
    "bold": "bold",
}

# CAT ASCII FRAMES for LOADER
CAT_FRAMES = [
    r''' /\_/\  
 ( o.o )''',
    r''' /\_/\  
 ( -.- )''',
    r''' /\_/\  
 ( o.o )''',
    r''' /\_/\  
 ( -.- )~''',
    r''' /\_/\  
 ( o.o )~''',
    r''' /\_/\  
 ( -.- )''',
]

def ascii_loader(message, duration=2):
    from time import sleep
    t_end = time.time() + duration
    i = 0
    while time.time() < t_end:
        frame = CAT_FRAMES[i % len(CAT_FRAMES)]
        sys.stdout.write(f"\r{message}\n{frame}\033[K")
        sys.stdout.flush()
        sleep(0.19)
        i += 1
        sys.stdout.write("\033[F" * 2)
    sys.stdout.write(f"\r{message}\n{CAT_FRAMES[0]}\n")
    sys.stdout.flush()

def color(text, c, bold=False, bg=None):
    # Centralized color function, always use this!
    if not RICH_AVAILABLE:
        codes = {
            'cyan': '36', 'magenta': '35', 'yellow': '33', 'green': '32', 'red': '31', 'blue': '34', 'white': '37'
        }
        style = []
        if bold: style.append('1')
        if c in codes: style.append(codes[c])
        if bg == 'black': style.append('40')
        if not style: style = ['0']
        return f"\033[{';'.join(style)}m{text}\033[0m"
    tag = c
    if bold: tag = f"bold {c}"
    if bg: tag += f" on {bg}"
    return f"[{tag}]{text}[/{tag}]"

def print_banner():
    try:
        val = banner() if callable(banner) else banner
        val = str(val or '').strip()
        if val:
            border = color("─" * 65, COLOR_PALETTE["accent"], bold=True)
            if console:
                console.print(border)
                console.print(color(val, COLOR_PALETTE["success"], bold=True))
                console.print(border)
            else:
                print(border)
                print(color(val, COLOR_PALETTE["success"], bold=True))
                print(border)
    except Exception as e:
        print(color(f"[!] Failed to print banner: {e}", COLOR_PALETTE["fail"], bold=True, bg="black"))

def print_usage():
    msg = color("[VENO]", COLOR_PALETTE["primary"], bold=True) + color(" Usage: set options, show options, run, help, clear, exit", "white")
    tail = color("Type 'help' for full command details.\n", COLOR_PALETTE["accent"], bold=True)
    if console: console.print(msg); console.print(tail)
    else: print(msg); print(tail)

def print_help():
    lines = [
        "\n" + color("VENO Automated Recon Shell - Full Help", COLOR_PALETTE["accent"], bold=True) + "\n",
        "  " + color("show options", COLOR_PALETTE["primary"], bold=True),
        "      Prints all current settings and scan parameters.",
        "  " + color("set <option> <value>", COLOR_PALETTE["primary"], bold=True),
        "      Set a scan option. Options include:",
        "        " + color("domain", COLOR_PALETTE["warn"], bold=True) + "       - Target domain to scan (e.g. set domain example.com)",
        "        " + color("output", COLOR_PALETTE["warn"], bold=True) + "       - Output directory for results (default: output)",
        "        " + color("threads", COLOR_PALETTE["warn"], bold=True) + "      - Number of threads/tools to use (e.g. set threads 10)",
        "        " + color("wordlist", COLOR_PALETTE["warn"], bold=True) + "     - Custom wordlist path for fuzzing/discovery",
        "        " + color("subscan", COLOR_PALETTE["warn"], bold=True) + "      - true/false to enable/disable subdomain scan",
        "        " + color("intensity", COLOR_PALETTE["warn"], bold=True) + "    - Scan profile (see below)",
        "      Example: set domain example.com",
        "      Example: set intensity deep",
        "      Example: set threads 50\n",
        "  " + color("run", COLOR_PALETTE["primary"], bold=True),
        "      Launches the full scan with the current config.",
        "  " + color("save config <filename>", COLOR_PALETTE["primary"], bold=True),
        "      Saves current config to a file.",
        "  " + color("load config <filename>", COLOR_PALETTE["primary"], bold=True),
        "      Loads config from a file.",
        "  " + color("timer", COLOR_PALETTE["primary"], bold=True),
        "      Show session elapsed time.",
        "  " + color("clear", COLOR_PALETTE["primary"], bold=True),
        "      Clears the screen and reprints the VENO banner.",
        "  " + color("help", COLOR_PALETTE["primary"], bold=True),
        "      Show this help message at any time.",
        "  " + color("-h, --help", COLOR_PALETTE["primary"], bold=True),
        "      Show basic usage summary at any time.",
        "  " + color("exit, quit", COLOR_PALETTE["primary"], bold=True),
        "      Leave the shell.\n",
        color("Scan Intensities (affect wordlist, tools, threads):", COLOR_PALETTE["accent"], bold=True) + "\n"
    ]
    for key, profile in SCAN_INTENSITIES.items():
        features = []
        if profile.get("run_nuclei_full"): features.append("extended nuclei")
        if profile.get("dalfox"): features.append("xss")
        if profile.get("xsstrike"): features.append("xsstrike")
        if profile.get("run_sqlmap"): features.append("sqlmap")
        features_str = " | ".join(features)
        lines.append(
            f"    {color(key, COLOR_PALETTE['warn'], bold=True)}: wordlist={os.path.basename(profile['wordlist']) if 'wordlist' in profile else 'N/A'}, threads={profile['threads'] if 'threads' in profile else 'N/A'}"
            + (", " + features_str if features_str else ""))
    lines += [
        "\n  " + color("Example Usage:", COLOR_PALETTE["accent"], bold=True),
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
    msg = color("\nCurrent VENO options:", COLOR_PALETTE["success"], bold=True)
    if console: console.print(msg)
    else: print(msg)
    for k, v in config.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                print(color(f"  {k}.{sk}: {sv}", COLOR_PALETTE["primary"]))
        else:
            print(color(f"  {k}: {v}", COLOR_PALETTE["primary"]))
    print("")

def merge_intensity(config, intensity):
    if intensity not in SCAN_INTENSITIES:
        msg = color(f"Unknown intensity: {intensity}. Available: {', '.join(SCAN_INTENSITIES)}", COLOR_PALETTE["fail"], bold=True, bg="black")
        if console: console.print(msg)
        else: print(msg)
        return
    profile = SCAN_INTENSITIES[intensity]
    config["intensity"] = intensity
    config["wordlist"] = profile.get("wordlist", "")
    config["scan_config"]["threads"] = profile.get("threads", 20)
    for key in profile:
        if key in ("wordlist", "threads"): continue
        config["scan_config"][key] = profile[key]

def ensure_output_dirs(config):
    domain = config.get("domain")
    output_dir = config.get("output_dir", "output")
    if domain:
        path = os.path.join(output_dir, domain)
        os.makedirs(path, exist_ok=True)

def safe_path(path):
    return os.path.abspath(os.path.expanduser(path))

def save_config(config, filename):
    try:
        filename = safe_path(filename)
        if os.path.exists(filename):
            confirm = input(color(f"[VENO] {filename} exists. Overwrite? (y/N): ", COLOR_PALETTE["fail"], bold=True))
            if confirm.strip().lower() not in ("y", "yes"):
                print(color("[VENO] Save cancelled.", COLOR_PALETTE["warn"], bold=True))
                return
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(color(f"[VENO] Config saved to {filename}", COLOR_PALETTE["success"], bold=True))
    except Exception as e:
        print(color(f"[VENO] Failed to save config: {e}", COLOR_PALETTE["fail"], bold=True, bg="black"))

def load_config(config, filename):
    try:
        filename = safe_path(filename)
        with open(filename, 'r') as f:
            loaded = json.load(f)
            config.clear()
            config.update(loaded)
        print(color(f"[VENO] Config loaded from {filename}", COLOR_PALETTE["success"], bold=True))
    except Exception as e:
        print(color(f"[VENO] Failed to load config: {e}", COLOR_PALETTE["fail"], bold=True, bg="black"))

def validate_domain(domain):
    pat = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,}$")
    return bool(pat.match(domain))

def validate_threads(threads):
    try:
        n = int(threads)
        return 1 <= n <= 1000
    except Exception:
        return False

COMMAND_LOG = []

def main():
    session_start = time.time()
    try:
        check_dependencies()
        msg = color("🔥 [VENO] ALL DEPENDENCIES SATISFIED! 🔥", COLOR_PALETTE["success"], bold=True, bg="black")
        border = color("─" * 65, COLOR_PALETTE["accent"], bold=True)
        if console:
            console.print(border)
            console.print(msg)
            console.print(border)
        else:
            print(border)
            print(msg)
            print(border)
    except Exception as e:
        print(color(f"[VENO] Dependency check failed: {e}", COLOR_PALETTE["fail"], bold=True, bg="black"))
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

    if default_intensity in SCAN_INTENSITIES:
        merge_intensity(config, default_intensity)

    while True:
        try:
            prompt_str = color("veno", COLOR_PALETTE["accent"], bold=True) + color(" > ", COLOR_PALETTE["success"], bold=True)
            if console:
                cmd = Prompt.ask(prompt_str)
            else:
                cmd = input(prompt_str)
            cmd = cmd.strip()
        except (EOFError, KeyboardInterrupt):
            if console:
                console.print(color("Bye.", COLOR_PALETTE["accent"], bold=True))
            else:
                print(color("Bye.", COLOR_PALETTE["accent"], bold=True))
            sys.exit(0)

        if not cmd:
            continue
        COMMAND_LOG.append(cmd)

        if cmd in ("exit", "quit"):
            if console:
                console.print(color("Bye.", COLOR_PALETTE["accent"], bold=True))
            else:
                print(color("Bye.", COLOR_PALETTE["accent"], bold=True))
            break

        elif cmd == "help":
            print_help()
        elif cmd in ("-h", "--help"):
            print_usage()
        elif cmd in ("show options", "options"):
            show_options(config)
        elif cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
            print_usage()
            continue
        elif cmd.startswith("save config "):
            _, _, filename = cmd.partition(" ")
            filename = filename.strip().split(" ", 1)[-1]
            if filename:
                save_config(config, filename)
            else:
                print(color("[VENO] Usage: save config <filename>", COLOR_PALETTE["fail"], bold=True, bg="black"))
        elif cmd.startswith("load config "):
            _, _, filename = cmd.partition(" ")
            filename = filename.strip().split(" ", 1)[-1]
            if filename:
                load_config(config, filename)
            else:
                print(color("[VENO] Usage: load config <filename>", COLOR_PALETTE["fail"], bold=True, bg="black"))
        elif cmd == "timer":
            elapsed = time.time() - session_start
            mins, secs = divmod(int(elapsed), 60)
            print(color(f"[VENO] Session time: {mins} min {secs} sec", COLOR_PALETTE["warn"], bold=True))
        elif cmd.startswith("set "):
            parts = cmd.split()
            if len(parts) < 3:
                print(color("Usage: set <option> <value>", COLOR_PALETTE["fail"], bold=True, bg="black"))
                continue
            option = parts[1]
            value = " ".join(parts[2:])
            if option == "threads":
                if not validate_threads(value):
                    print(color("[VENO] threads must be an integer between 1 and 1000", COLOR_PALETTE["fail"], bold=True, bg="black"))
                    continue
                config["scan_config"]["threads"] = int(value)
            elif option == "output":
                config["output_dir"] = safe_path(value)
            elif option == "wordlist":
                if not os.path.isfile(value):
                    print(color(f"[VENO] Wordlist not found: {value}", COLOR_PALETTE["fail"], bold=True, bg="black"))
                    continue
                config["wordlist"] = value
            elif option == "domain":
                if not validate_domain(value):
                    print(color("[VENO] Invalid domain name.", COLOR_PALETTE["fail"], bold=True, bg="black"))
                    continue
                config["domain"] = value
            elif option == "subscan":
                config["subscan"] = value.lower() == "true"
            elif option == "intensity":
                merge_intensity(config, value)
            else:
                print(color(f"[VENO] Unknown option: {option}", COLOR_PALETTE["fail"], bold=True, bg="black"))
        elif cmd == "run":
            if not config.get("domain"):
                print(color("[VENO] Please set a valid domain before running.", COLOR_PALETTE["fail"], bold=True, bg="black"))
                continue
            ensure_output_dirs(config)
            ascii_loader(color("[VENO] Starting scan...", COLOR_PALETTE["warn"], bold=True), duration=1)
            try:
                full_scan(config)
            except Exception as e:
                print(color(f"[VENO] Scan failed: {e}", COLOR_PALETTE["fail"], bold=True, bg="black"))
        elif cmd == "meme" and HAS_MEMES:
            meme = get_ascii_meme()
            if console:
                console.print(meme)
            else:
                print(meme)
        elif cmd == "insult" and HAS_MEMES:
            insult = get_insult()
            if console:
                console.print(insult)
            else:
                print(insult)
        else:
            print(color(f"[VENO] Unknown command: {cmd}", COLOR_PALETTE["fail"], bold=True, bg="black"))

if __name__ == "__main__":
    main()
