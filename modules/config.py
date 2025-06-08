import json
import os
import sys

def supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

RED = "\033[1;31m" if supports_color() else ""
GREEN = "\033[1;32m" if supports_color() else ""
CYAN = "\033[1;36m" if supports_color() else ""
RESET = "\033[0m" if supports_color() else ""

def save_config(outdir, selected_tools, wordlist, scan_config, recursion_depth, subdomain_scan):
    config = {
        "tools": selected_tools,
        "wordlist": wordlist,
        "scan_config": scan_config,
        "recursion_depth": recursion_depth,
        "subdomain_scan": subdomain_scan
    }
    config_path = os.path.join(outdir, "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        if supports_color():
            print(f"{GREEN}[✔] Configuration saved to {config_path}{RESET}")
    except Exception as e:
        print(f"{RED}[!] Failed to save config: {e}{RESET}", file=sys.stderr)
        raise

def load_config(outdir):
    config_path = os.path.join(outdir, "config.json")
    if not os.path.exists(config_path):
        if supports_color():
            print(f"{CYAN}[i] No config found at {config_path}, returning empty config.{RESET}")
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"{RED}[!] Failed to load config: {e}{RESET}", file=sys.stderr)
        raise
