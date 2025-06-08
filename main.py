import sys
import logging
import subprocess
from modules.banner import BANNER  # If a function, call as BANNER(), else print(BANNER)
from modules.scanner import full_scan
from modules.scan_intensity import SCAN_INTENSITIES
from modules.dependencies import check_dependencies

def print_banner():
    # Handles if BANNER is a string or a function
    print(BANNER() if callable(BANNER) else BANNER)

def print_usage():
    print("\033[1;35m[VENO]\033[0m Usage: set options, show options, run, help, update, exit")
    print("Type '\033[1;36mhelp\033[0m' for full command details.\n")

def print_help():
    print("\n\033[1;35mVENO Automated Recon Shell - Full Help\033[0m\n")
    print("  \033[1;36mshow options\033[0m\n      Prints all current settings and scan parameters.")
    print("  \033[1;36mset <option> <value>\033[0m\n      Set a scan option. Options include:")
    print("        \033[1;33mdomain\033[0m       - Target domain to scan (e.g. set domain example.com)")
    print("        \033[1;33moutput\033[0m       - Output directory for results (default: output)")
    print("        \033[1;33mthreads\033[0m      - Number of threads/tools to use (e.g. set threads 10)")
    print("        \033[1;33mwordlist\033[0m     - Custom wordlist path for fuzzing/discovery")
    print("        \033[1;33msubscan\033[0m      - true/false to enable/disable subdomain scan")
    print("        \033[1;33mintensity\033[0m    - Scan profile (see below)")
    print("      Example: set domain example.com")
    print("      Example: set intensity deep")
    print("      Example: set threads 50\n")
    print("  \033[1;36mrun\033[0m\n      Launches the full scan with the current config. Results and report will be saved to your output directory.")
    print("  \033[1;36mupdate\033[0m\n      Updates VENO to the latest version using git and pip.")
    print("  \033[1;36mhelp\033[0m\n      Show this help message at any time.")
    print("  \033[1;36mexit, quit\033[0m\n      Leave the shell.\n")
    print("  \033[1;35mScan Intensities (affect wordlist, tools, threads):\033[0m\n")
    for key, profile in SCAN_INTENSITIES.items():
        features = []
        if profile.get("run_nuclei_full"): features.append("extended nuclei")
        if profile.get("dalfox"): features.append("xss")
        if profile.get("xsstrike"): features.append("xsstrike")
        if profile.get("run_sqlmap"): features.append("sqlmap")
        features_str = " | ".join(features)
        print(f"    \033[1;33m{key}\033[0m: wordlist={profile['wordlist'].split('/')[-1]}, threads={profile['threads']}" +
              (", " + features_str if features_str else ""))
    print("\n  \033[1;35mExample Usage:\033[0m")
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
        print(f"Unknown intensity: {intensity}. Available: {', '.join(SCAN_INTENSITIES)}")
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
    print("\n\033[1;36m[VENO] Updating...\033[0m")
    try:
        subprocess.run(['git', 'pull'], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', 'requirements.txt'], check=True)
        print("\033[1;32m[VENO] Update complete! Please restart VENO if libraries were upgraded.\033[0m\n")
    except Exception as e:
        print(f"\033[1;31m[VENO] Update failed: {e}\033[0m\n")

def main():
    # Dependency check ONCE, only print if fails or successful
    try:
        check_dependencies()
        print("\033[1;32m[✓] All required tools are installed.\033[0m")
    except Exception as e:
        print(f"\033[1;31m[VENO]\033[0m Dependency check failed: {e}")
        sys.exit(3)

    print_banner()
    print_usage()

    # Default config — must match available intensities!
    default_intensity = "normal"
    config = {
        "domain": "",
        "output_dir": "output",
        "subscan": True,
        "intensity": default_intensity,
        "scan_config": {
            "threads": 10,
        },
        "wordlist": "",
    }
    merge_intensity(config, default_intensity)

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

        elif cmd == "update":
            update_veno()

        elif cmd.startswith("set "):
            parts = cmd.split()
            if len(parts) < 3:
                print("Usage: set <option> <value>")
                continue
            option = parts[1]
            value = " ".join(parts[2:])
            if option == "threads":
                try:
                    config["scan_config"]["threads"] = int(value)
                except ValueError:
                    print("threads must be an integer")
            elif option == "output":
                config["output_dir"] = value
            elif option == "wordlist":
                config["wordlist"] = value
            elif option == "domain":
                config["domain"] = value
            elif option == "subscan":
                config["subscan"] = value.lower() in ("yes", "true", "1", "on")
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
                print(f"\033[1;35m[VENO]\033[0m Starting full scan for \033[1;36m{domain}\033[0m (intensity: {config['intensity']})")
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
