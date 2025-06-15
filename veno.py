import sys
import logging
import os
import json
import time
import re
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from rich.console import Console
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
    console = Console()
except ImportError as exc:
    RICH_AVAILABLE = False
    console = None
    logger.warning(f"Failed to import rich: {exc}")

try:
    from modules.banner import banner
except ImportError as exc:
    banner = lambda: "VENO Automated Recon Shell"
    logger.warning(f"Failed to import banner: {exc}")

try:
    from modules.scanner import run_scanner
except ImportError as exc:
    logger.error(f"Scanner module not available: {exc}")
    raise ImportError(f"[!] Scanner module not available: {exc}")

try:
    from modules.scan_intensity import SCAN_INTENSITIES
except ImportError as exc:
    SCAN_INTENSITIES = {}
    logger.warning(f"Failed to import scan_intensity: {exc}")

try:
    from modules.dependencies import check_dependencies
except ImportError as exc:
    def check_dependencies(config=None):
        logger.warning("Dependencies module unavailable")
    logger.warning(f"Failed to import dependencies: {exc}")

try:
    from modules.memes import get_ascii_meme, get_insult
    HAS_MEMES = True
except ImportError as exc:
    HAS_MEMES = False
    get_ascii_meme = lambda: "¯\\_(ツ)_/¯"
    get_insult = lambda: ""
    logger.warning(f"Failed to import memes: {exc}")

def color(text, c, bold=False, bg=None):
    if not RICH_AVAILABLE:
        codes = {
            'cyan': '36', 'magenta': '35', 'yellow': '33', 'green': '32',
            'red': '31', 'blue': '34', 'white': '37'
        }
        style = []
        if bold:
            style.append('1')
        if c in codes:
            style.append(codes[c])
        if bg == 'black':
            style.append('40')
        if not style:
            style.append('0')
        return f"\033[{';'.join(style)}m{text}\033[0m"
    tag = c
    if bold and c:
        tag = f"bold {c}"
    if bg:
        tag += f" on {bg}"
    return f"[{tag}]{text}[/{tag}]"

def print_banner():
    try:
        val = banner() if callable(banner) else banner
        val = str(val).strip()
        if val:
            if console:
                console.print(color(val, "green", bold=True))
            else:
                print(color(val, "green", bold=True))
    except Exception as exc:
        logger.error(f"Failed to print banner: {exc}\n{traceback.format_exc()}")
        if console:
            console.print(color("[VENO] Automated Recon Shell", "cyan", bold=True))
        else:
            print(color("[VENO] Automated Recon Shell", "cyan", bold=True))

def print_usage():
    msg = color("[VENO]", "cyan", bold=True) + color(" Usage: set <option> <value>, show options, run, help, clear, exit", "white")
    tail = color("Type 'help' for full command details.\n", "green", bold=True)
    if console:
        console.print(msg)
        console.print(tail)
    else:
        print(msg)
        print(tail)

def print_help():
    help_text = f"""
{color('VENO Automated Recon Shell - Full Help', 'magenta', bold=True)}

{color('show options', 'cyan')}      - Prints all current settings.
{color('set <option> <value>', 'cyan')} - Set scan options:
  - {color('domain', 'yellow', bold=True)}     - Target domain (e.g., example.com)
  - {color('output_dir', 'yellow')} - Output directory (default: 'output')
  - {color('threads', 'yellow')}    - Threads (1-1000, default: 50)
  - {color('wordlist', 'yellow')}   - Custom wordlist path
  - {color('subscan', 'yellow')}    - true/false for subdomains (default: true/false)
  - {color('intensity', 'yellow')}  - Scan profile: light, medium, heavy (default: medium)
  - {color('dir_fuzz_tool', 'yellow')} - Fuzz tool: ffuf, dirsearch (default: ffuf)

    Example: set domain example.com
    Example: set intensity heavy

{color('run', 'cyan')}              - Launches scan with current config.
{color('save config <filename>', 'cyan')} - Saves config to file.
{color('timer', 'cyan')}            - Shows session elapsed time.
{color('clear', 'cyan')}            - Clears screen.
{color('help', 'cyan')}             - Shows this help.
{color('exit', 'cyan')} or {color('quit', 'cyan')} - Exits shell.

{color('Available dir_fuzz_tool Options:', 'magenta', bold=True)}:
  - ffuf: Fast fuzzing tool (default)
  - dirsearch: Comprehensive directory enumeration

{color('Scan Intensities:', 'magenta', bold=True)}:
"""

    for key, profile in SCAN_INTENSITIES.items():
        features = []
        if profile.get("run_nuclei_full"):
            features.append("extended nuclei")
        if profile.get("dalfox"):
            features.append("xss")
        if profile.get("xsstrike"):
            features.append("xsstrike")
        if profile.get("run_sqlmap"):
            features.append("sqlmap")
        features_str = " | ".join(features)

        help_text += f"  {color(key, 'yellow', bold=True)}: wordlist={os.path.basename(profile.get('wordlist', 'N/A'))}, "
        help_text += f"threads={profile.get('threads', 'N/A')}"
        if features_str:
            help_text += f", {features_str}"
        help_text += "\n"

    help_text += f"""
{color('Example Usage:', 'magenta', bold=True)}:
  set domain example.com
  set intensity medium
  set threads 20
  set dir_fuzz_tool ffuf
  run
"""

    if console:
        console.print(color(help_text, "cyan"))
    else:
        print(color(help_text, "cyan"))

def show_options(config):
    core_keys = ['domain', 'output_dir', 'threads', 'subscan', 'intensity', 'dir_fuzz_tool']
    msg = color("\nCurrent VENO Config:", "green", bold=True)
    if console:
        console.print(msg)
        for k in core_keys:
            console.print(color(f"  {k}: {config.get(k, 'N/A')}", "cyan"))
        console.print("")
    else:
        print(msg)
        for k in core_keys:
            print(color(f"  {k}: {config.get(k, 'N/A')}", "cyan"))
        print("")

def merge_intensity(config, intensity):
    if intensity not in SCAN_INTENSITIES:
        msg = color(f"Invalid intensity: {intensity}. Available: {', '.join(SCAN_INTENSITIES.keys())}", "red", bold=True)
        if console:
            console.print(msg)
        else:
            print(msg)
        return
    profile = SCAN_INTENSITIES[intensity]
    config["intensity"] = intensity
    for key, value in profile.items():
        config[key] = value

def ensure_output_dirs(config):
    domain = config.get("domain")
    output_dir = config.get("output_dir", "output")
    if domain:
        path = os.path.join(output_dir, domain)
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as exc:
            logger.error(f"Failed to create output directory {path}: {exc}")
            raise ValueError(f"Cannot create output directory: {path}")

def safe_path(path):
    return os.path.abspath(os.path.expanduser(path))

def save_config(config, filename):
    try:
        filename = safe_path(filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if os.path.exists(filename):
            confirm = input(
                color(f"[VENO] {filename} exists. Overwrite? (y/N): ", "yellow", bold=True)
            )
            if confirm.strip().lower() not in ["y", "yes"]:
                if console:
                    console.print(color("[VENO] Save cancelled", "yellow", bold=True))
                else:
                    print(color("[VENO] Save cancelled", "yellow", bold=True))
                return
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        if console:
            console.print(color(f"[VENO] Config saved to {filename}", "green", bold=True))
        else:
            print(color(f"[VENO] Config saved to {filename}", "green", bold=True))
    except OSError as exc:
        error_msg = f"Failed to save config: {str(exc)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        if console:
            console.print(color(f"[VENO] {error_msg}", "red", bold=True))
        else:
            print(color(f"[VENO] {error_msg}", "red", bold=True))

def validate_domain(domain):
    pat = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.[A-Za-z]{2,}$")
    return bool(pat.match(domain))

def validate_threads(value):
    try:
        n = int(value)
        return bool(1 <= n <= 1000)
    except ValueError:
        return False

def validate_dir_fuzz_tool(value):
    return value in ["ffuf", "dirsearch"]

def main():
    session_start = time.time()
    try:
        check_dependencies()
        msg = color("[VENO] All dependencies satisfied! ✅", "green", bold=True)
        border = color("─" * 65, "magenta", bold=True)
        if console:
            console.print(border)
            console.print(msg)
            console.print(border)
        else:
            print(border)
            print(msg)
            print(border)
    except Exception as exc:
        err = f"Dependency check failed: {exc}\n{traceback.format_exc()}"
        logger.error(err)
        if console:
            console.print(color(f"[VENO] {err}", "red", bold=True))
        else:
            print(color(f"[VENO] {err}", "red", bold=True))
        sys.exit(2)

    print_banner()
    if HAS_MEMES:
        if console:
            console.print(get_insult())
        else:
            print(get_insult())
    print_usage()

    default_intensity = "medium"
    config = {
        "domain": "",
        "output_dir": "output",
        "subscan": True,
        "intensity": default_intensity,
        "dir_fuzz_tool": "ffuf",
        "threads": 20,
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt"
    }

    if default_intensity in SCAN_INTENSITIES:
        merge_intensity(config, default_intensity)


    while True:
        try:
            prompt_str = color("[VENO", "magenta", bold=True) + color("] > ", "green", bold=True)
            if console:
                cmd = Prompt.ask(prompt_str)
            else:
                cmd = input(prompt_str)
            cmd = cmd.strip()
        except (EOFError, KeyboardInterrupt):
            bye_msg = color("Bye.", "magenta", bold=True)
            if console:
                console.print(bye_msg)
            else:
                print(bye_msg)
            sys.exit(0)

        if not cmd:
            continue

        try:
            if cmd in ("exit", "quit"):
                bye_msg = color("Bye.", "magenta", bold=True)
                if console:
                    console.print(bye_msg)
                else:
                    print(bye_msg)
                break

            elif cmd == "help":
                print_help()

            elif cmd in ("show options", "options"):
                show_options(config)

            elif cmd == "clear":
                os.system('cls' if os.name == 'nt' else "clear")
                print_banner()
                print_usage()

            elif cmd.startswith("save config"):
                _, _, filename = cmd.partition("save config")
                filename = filename.strip()
                if filename:
                    save_config(config, filename)
                else:
                    err = color("[VENO] Usage: save config <filename>", "red", bold=True)
                    console.print(err) if console else print(err)

            elif cmd == "timer":
                elapsed = time.time() - session_start
                mins, secs = divmod(int(elapsed), 60)
                msg = color(f"[VENO] Session time: {mins}m {secs}s", "yellow", bold=True)
                console.print(msg) if console else print(msg)

            elif cmd.startswith("set "):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 3:
                    err = color("[VENO] Usage: set <option> <value>", "red", bold=True)
                    console.print(err) if console else print(err)
                    continue

                option, value = parts[1], parts[2]

                if option == "threads":
                    if not validate_threads(value):
                        err = color("[VENO] Threads must be 1-1000", "red", bold=True)
                        console.print(err) if console else print(err)
                        continue
                    config["threads"] = int(value)

                elif option == "output_dir":
                    config["output_dir"] = safe_path(value)

                elif option == "wordlist":
                    if not os.path.isfile(value):
                        err_msg = f"[VENO] Wordlist not found: {value}"
                        msg = color(err_msg, "red", bold=True)
                        console.print(msg) if console else print(msg)
                        continue
                    config["wordlist"] = value

                elif option == "domain":
                    if not validate_domain(value):
                        err = color("[VENO] Invalid domain name.", "red", bold=True)
                        console.print(err) if console else print(err)
                        continue
                    config["domain"] = value

                elif option == "subscan":
                    config["subscan"] = value.lower() == "true"

                elif option == "intensity":
                    merge_intensity(config, value)

                elif option == "dir_fuzz_tool":
                    if not validate_dir_fuzz_tool(value):
                        err = color("[VENO] dir_fuzz_tool must be 'ffuf' or 'dirsearch'", "red", bold=True)
                        console.print(err) if console else print(err)
                        continue
                    config["dir_fuzz_tool"] = value

                else:
                    err = color(f"[VENO] Unknown option: {option}", "red", bold=True)
                    console.print(err) if console else print(err)

            elif cmd == "run":
                if not config["domain"]:
                    err = color("[VENO] Error: Please set a valid domain.", "red", bold=True)
                    console.print(err) if console else print(err)
                    continue

                ensure_output_dirs(config)
                error_log = os.path.join(config["output_dir"], config["domain"], "errors.log")
                try:
                    os.makedirs(os.path.dirname(error_log), exist_ok=True)
                except OSError as exc:
                    logger.error(f"Failed to create error log directory: {exc}\n{traceback.format_exc()}")
                    msg = color(f"[VENO] Failed to create error log directory: {exc}", "red", bold=True)
                    console.print(msg) if console else print(msg)
                    continue

                console.print(color("[VENO] Starting scan...", "yellow", bold=True)) if console else print(color("[VENO] Starting scan...", "yellow", bold=True))
                try:
                    if HAS_MEMES:
                        meme = get_ascii_meme()
                        console.print(meme) if console else print(meme)

                    run_scanner(config["domain"], config, {})

                    msg = color("[VENO] Scan completed successfully.", "green", bold=True)
                    console.print(msg) if console else print(msg)
                    if HAS_MEMES:
                        console.print(get_insult()) if console else print(get_insult())

                except Exception as exc:
                    error_msg = f"Scan failed: {exc}\n{traceback.format_exc()}"
                    try:
                        with open(error_log, "a", encoding='utf-8') as f:
                            f.write(error_msg + "\n")
                    except OSError as e:
                        logger.error(f"Failed to write error log: {e}\n{traceback.format_exc()}")
                        msg = color(f"[VENO] Failed to write error log: {e}", "red", bold=True)
                        console.print(msg) if console else print(msg)

                    msg = color(f"[VENO] {error_msg}", "red", bold=True)
                    console.print(msg) if console else print(msg)

            else:
                err = color(f"[VENO] Unknown command: {cmd}", "red", bold=True)
                console.print(err) if console else print(err)

        except Exception as exc:
            error_msg = f"Command '{cmd}' failed: {exc}\n{traceback.format_exc()}"
            logger.error(error_msg)
            msg = color(f"[VENO] {error_msg}", "red", bold=True)
            console.print(msg) if console else print(msg)


if __name__ == "__main__":
    main()
