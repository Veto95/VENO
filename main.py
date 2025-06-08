import sys
import logging
from modules.banner import BANNER
from modules.scanner import full_scan
from modules.scan_intensity import SCAN_INTENSITIES

print(BANNER)

def print_help():
    print("""
VENO Automated Recon Shell Commands:
    show options        Show current settings
    set <option> <val> Set an option (domain, output, threads, wordlist, banner_html, subdomains, intensity)
    run                Start the scan
    help               Show this help message
    exit, quit         Exit the shell

Scan intensities (affect wordlist/tools/threads): low, medium, high, max
""")

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
        print(f"Unknown intensity: {intensity}. Available: {', '.join(SCAN_INTENSITIES)}")
        return
    profile = SCAN_INTENSITIES[intensity]
    config["intensity"] = intensity
    config["wordlist"] = profile["wordlist"]
    config["scan_config"]["threads"] = profile["threads"]
    # Set per-tool booleans
    for key in profile:
        if key in ("wordlist", "threads"):
            continue
        config["scan_config"][key] = profile[key]

def main():
    # Default config
    config = {
        "domain": "",
        "output_dir": "output",
        "subdomains": True,
        "banner_html": "",
        "intensity": "medium",
        "scan_config": {
            "threads": 10,
        },
        "wordlist": "",
    }
    merge_intensity(config, "medium")

    print_help()

    while True:
        try:
            cmd = input("veno > ").strip()
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

        elif cmd == "show options":
            show_options(config)

        elif cmd.startswith("set "):
            parts = cmd.split()
            if len(parts) < 3:
                print("Usage: set <option> <value>")
                continue
            option = parts[1]
            value = " ".join(parts[2:])
            # Handle nested options & intensity
            if option == "threads":
                try:
                    config["scan_config"]["threads"] = int(value)
                except ValueError:
                    print("threads must be an integer")
            elif option == "output":
                config["output_dir"] = value
            elif option == "wordlist":
                config["wordlist"] = value
            elif option == "banner_html":
                config["banner_html"] = value
            elif option == "domain":
                config["domain"] = value
            elif option == "subdomains":
                config["subdomains"] = value.lower() in ("yes", "true", "1", "on")
            elif option == "intensity":
                merge_intensity(config, value)
            else:
                print(f"Unknown option: {option}")
            show_options(config)

        elif cmd == "run":
            domain = config.get("domain")
            if not domain:
                print("Set a domain first: set domain <example.com>")
                continue

            try:
                logging.basicConfig(
                    filename=f"{config['output_dir']}/{domain}/veno.log",
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s"
                )
                print(f"\033[1;35m[VENO]\033[0m Starting full scan for \033[1;36m{domain}\033[0m")
                full_scan(domain, config)
                print(f"\033[1;32m[VENO]\033[0m Scan completed for \033[1;36m{domain}\033[0m")
                print(f"Report: {config['output_dir']}/{domain}/report.html")
            except KeyboardInterrupt:
                print(f"\033[1;31m[VENO]\033[0m Scan interrupted by user!")
                sys.exit(1)
            except Exception as e:
                print(f"\033[1;31m[VENO]\033[0m Fatal error: {e}")
                sys.exit(2)

        else:
            print("Unknown command. Type 'help' for options.")

if __name__ == "__main__":
    main()
