import sys
import logging
import subprocess
import os
import json
import time
import re

try:
    import readline  # for colored prompt/history if available
except ImportError:
    pass

from modules.banner import banner # Can be string or function!
from modules.scanner import full_scan
from modules.scan_intensity import SCAN_INTENSITIES
from modules.dependencies import check_dependencies

# --- ASCII Loader Animation (Toggled by user) ---
ASCII_ANIM_ENABLED = True
ASCII_FRAMES = [
    "🐍    ", " 🐍   ", "  🐍  ", "   🐍 ", "    🐍", "   🐍 ", "  🐍  ", " 🐍   "
]

def ascii_loader(message, duration=2):
    # Only runs if enabled
    if not ASCII_ANIM_ENABLED:
        print(message)
        return
    from time import sleep
    import sys
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

# --- Color helpers ---
def color(text, c):
    colors = {
        'cyan': '\033[1;36m', 'magenta': '\033[1;35m', 'yellow': '\033[1;33m',
        'green': '\033[1;32m', 'red': '\033[1;31m', 'reset': '\033[0m', 
        'blue': '\033[1;34m', 'bold': '\033[1m'
    }
    return f"{colors.get(c, '')}{text}{colors['reset']}"

def print_banner():
    print(banner() if callable(banner) else banner)

def print_usage():
    print(color("[VENO]", "magenta") + " Usage: set options, show options, run, help, update, clear, exit")
    print("Type " + color("'help'", "cyan") + " for full command details.\n")

def print_help():
    print("\n" + color("VENO Automated Recon Shell - Full Help", "magenta") + "\n")
    print("  " + color("show options", "cyan"))
    print("      Prints all current settings and scan parameters.")
    print("  " + color("set <option> <value>", "cyan"))
    print("      Set a scan option. Options include:")
    print("        " + color("domain", "yellow") + "       - Target domain to scan (e.g. set domain example.com)")
    print("        " + color("output", "yellow") + "       - Output directory for results (default: output)")
    print("        " + color("threads", "yellow") + "      - Number of threads/tools to use (e.g. set threads 10)")
    print("        " + color("wordlist", "yellow") + "     - Custom wordlist path for fuzzing/discovery")
    print("        " + color("subscan", "yellow") + "      - true/false to enable/disable subdomain scan")
    print("        " + color("intensity", "yellow") + "    - Scan profile (see below)")
    print("      Example: set domain example.com")
    print("      Example: set intensity deep")
    print("      Example: set threads 50\n")
    print("  " + color("run", "cyan"))
    print("      Launches the full scan with the current config. Results and report will be saved to your output directory.")
    print("  " + color("update", "cyan"))
    print("      Updates VENO to the latest version using git and pip.")
    print("  " + color("save config <filename>", "cyan"))
    print("      Saves current config to a file.")
    print("  " + color("load config <filename>", "cyan"))
    print("      Loads config from a file.")
    print("  " + color("toggle ascii", "cyan"))
    print("      Enable/disable ASCII loader animation for long ops.")
    print("  " + color("timer", "cyan"))
    print("      Show session elapsed time.")
    print("  " + color("clear", "cyan"))
    print("      Clears the screen and reprints the VENO banner.")
    print("  " + color("help", "cyan"))
    print("      Show this help message at any time.")
    print("  " + color("-h, --help", "cyan"))
    print("      Show basic usage summary at any time.")
    print("  " + color("exit, quit", "cyan"))
    print("      Leave the shell.\n")
    print(color("Scan Intensities (affect wordlist, tools, threads):", "magenta") + "\n")
    for key, profile in SCAN_INTENSITIES.items():
        features = []
        if profile.get("run_nuclei_full"): features.append("extended nuclei")
        if profile.get("dalfox"): features.append("xss")
        if profile.get("xsstrike"): features.append("xsstrike")
        if profile.get("run_sqlmap"): features.append("sqlmap")
        features_str = " | ".join(features)
        print(f"    {color(key, 'yellow')}: wordlist={profile['wordlist'].split('/')[-1]}, threads={profile['threads']}" +
              (", " + features_str if features_str else ""))
    print("\n  " + color("Example Usage:", "magenta"))
    print("      set domain example.com")
    print("      set intensity normal")
    print("      set threads 20")
    print("      run\n")

def show_options(config):
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
        print(color(f"Unknown intensity: {intensity}. Available: {', '.join(SCAN_INTENSITIES)}", "red"))
        return
    profile = SCAN_INTENSITIES[intensity]
    config["intensity"] = intensity
    config["wordlist"] = profile["wordlist"]
    config["scan_config"]["threads"] = profile["threads"]
    for key in profile:
        if key in ("wordlist", "threads"):
            continue
        config["scan_config"][key] = profile[key]

def update_veno():
    print("\n" + color("[VENO] Updating...", "cyan"))
    try:
        subprocess.run(['git', 'pull'], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', 'requirements.txt'], check=True)
        print(color("[VENO] Update complete! Please restart VENO if libraries were upgraded.", "green") + "\n")
    except Exception as e:
        print(color(f"[VENO] Update failed: {e}", "red") + "\n")

def ensure_output_dirs(config):
    domain = config.get("domain")
    output_dir = config.get("output_dir", "output")
    if domain:
        path = os.path.join(output_dir, domain)
        os.makedirs(path, exist_ok=True)

def save_config(config, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(color(f"[VENO] Config saved to {filename}", "green"))
    except Exception as e:
        print(color(f"[VENO] Failed to save config: {e}", "red"))

def load_config(config, filename):
    try:
        with open(filename, 'r') as f:
            loaded = json.load(f)
            config.clear()
            config.update(loaded)
        print(color(f"[VENO] Config loaded from {filename}", "green"))
    except Exception as e:
        print(color(f"[VENO] Failed to load config: {e}", "red"))

def validate_domain(domain):
    # Accepts FQDNs, subdomains, not IPs
    pat = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,}$")
    return bool(pat.match(domain))

def validate_threads(threads):
    try:
        n = int(threads)
        return 1 <= n <= 1000
    except Exception:
        return False

def main():
    # --- Session Timer ---
    session_start = time.time()

    # --- Self-update prompt ---
    try:
        check_dependencies()
        print(color("[✓] All required tools are installed.", "green"))
    except Exception as e:
        print(color(f"[VENO] Dependency check failed: {e}", "red"))
        sys.exit(3)

    # Offer update on start
    resp = input(color("[VENO] Check for updates on start? (Y/n): ", "cyan")).strip().lower()
    if resp in ("", "y", "yes"):
        update_veno()

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

    global ASCII_ANIM_ENABLED

    while True:
        try:
            prompt_str = color("veno", "magenta") + color(" > ", "cyan")
            cmd = input(prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting VENO.")
            sys.exit(0)

        if not cmd:
            continue

        if cmd in ("exit", "quit"):
            print("Bye.")
            break

        elif cmd == "help":
            print_help()
        elif cmd in ("-h", "--help"):
            print_usage()
        elif cmd == "show options":
            show_options(config)
        elif cmd == "update":
            update_veno()
        elif cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            print_banner()
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
        elif cmd == "toggle ascii":
            ASCII_ANIM_ENABLED = not ASCII_ANIM_ENABLED
            print(color(f"[VENO] ASCII animation {'enabled' if ASCII_ANIM_ENABLED else 'disabled'}", "green"))
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
                config["output_dir"] = value
            elif option == "wordlist":
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
                print(color(f"[VENO] Starting full scan for {domain} (intensity: {config['intensity']})", "magenta"))
                ascii_loader("[VENO] Starting scan..." if ASCII_ANIM_ENABLED else "[VENO] Scan running...", duration=2)
                full_scan(domain, config)
                print(color(f"[VENO] Scan completed for {domain}", "green"))
                print(color(f"Report: {os.path.join(config['output_dir'], domain, 'report.html')}", "yellow"))
            except KeyboardInterrupt:
                print(color("[VENO] Scan interrupted by user!", "red"))
                sys.exit(1)
            except Exception as e:
                print(color(f"[VENO] Fatal error: {e}", "red"))
                sys.exit(2)
        else:
            print(color("Unknown command. Type '-h' for usage or 'help' for full command details.", "red"))

if __name__ == "__main__":
    main()
