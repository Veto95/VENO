import os
import sys
import traceback
import warnings
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress unverified HTTPS warnings for a cleaner experience
with warnings.catch_warnings():
    try:
        import urllib3
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        urllib3.disable_warnings()
    except ImportError:
        pass

from modules.banner import banner, get_banner_html
from modules.dependencies import check_dependencies
from modules.domain_input import get_domains
from modules.scan_intensity import get_scan_intensity, suggest_tools
from modules.subdomain_scan import get_subdomain_scan_choice
from modules.wordlist import get_wordlist
from modules.config import save_config
from modules.scanner import full_scan

# ---- CONSTANTS ----
OUTPUT_DIR = "output"
SCANNED_DOMAINS = "scanned_domains.txt"
SCANNED_IPS = "scanned_ips.txt"
ERROR_LOG = "error.log"
MAX_THREADS = 5  # Tweak for your system!

# ---- UTILS ----
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_scanned_domains():
    scanned_path = os.path.join(OUTPUT_DIR, SCANNED_DOMAINS)
    if os.path.exists(scanned_path):
        with open(scanned_path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def log_error(message, domain=None):
    """Log error globally or per-domain."""
    if domain:
        dir_path = os.path.join(OUTPUT_DIR, domain)
        os.makedirs(dir_path, exist_ok=True)
        err_path = os.path.join(dir_path, "errors.log")
    else:
        err_path = os.path.join(OUTPUT_DIR, ERROR_LOG)
    with open(err_path, "a") as f:
        f.write(message + "\n")

def prompt_resume():
    while True:
        resp = input("Do you want to resume the last scan? [Y/n]: ").strip().lower()
        if resp in ("", "y", "yes"):
            return True
        elif resp in ("n", "no"):
            return False
        else:
            print("Invalid input. Please enter Y or N.")

def print_status(msg):
    print(f"\033[1;36m[VENO]\033[0m {msg}")

def print_success(msg):
    print(f"\033[1;32m[\u2713]\033[0m {msg}")

def print_error(msg):
    print(f"\033[1;31m[!]\033[0m {msg}")

# ---- MAIN SCAN FUNCTION ----
def scan_domain(domain, config, lock):
    """Scan a single domain and log progress/errors."""
    try:
        print_status(f"Scanning: {domain}")
        full_scan(domain, config)
        with lock:
            with open(os.path.join(OUTPUT_DIR, SCANNED_DOMAINS), "a") as f:
                f.write(domain + "\n")
    except Exception:
        print_error(f"Scan failed for {domain}. See output/{domain}/errors.log for details.")
        log_error(traceback.format_exc(), domain=domain)

# ---- MAIN ENTRY ----
def main():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        clear_screen()
        banner()
        print_status(f"OUTPUT DIRECTORY: \033[1;33m{OUTPUT_DIR}\033[0m")
        check_dependencies(OUTPUT_DIR)

        scanned_domains = get_scanned_domains()
        resume = False

        if scanned_domains:
            print_status("Existing scan detected.")
            resume = prompt_resume()

        print_status("DOMAIN INPUT")
        selected_domains = get_domains(OUTPUT_DIR)

        if resume:
            selected_domains = [d for d in selected_domains if d not in scanned_domains]
            if not selected_domains:
                print_success("All domains already scanned! Exiting.")
                return
            print_status(f"Resuming scan for remaining {len(selected_domains)} domains...")
        else:
            for fname in (SCANNED_DOMAINS, SCANNED_IPS):
                open(os.path.join(OUTPUT_DIR, fname), "w").close()

        print_status("SCAN INTENSITY")
        scan_config = get_scan_intensity(OUTPUT_DIR)

        print_status("SUBDOMAIN SCAN")
        subdomain_scan = get_subdomain_scan_choice(OUTPUT_DIR)

        print_status("WORDLIST SELECTION")
        wordlist = get_wordlist(OUTPUT_DIR)

        selected_tools = suggest_tools(scan_config, subdomain_scan)
        print_status(f"TOOL SELECTION (auto): \033[1;32m{', '.join(selected_tools)}\033[0m")

        config = {
            "output_dir": OUTPUT_DIR,
            "selected_tools": selected_tools,
            "wordlist": wordlist,
            "scan_config": scan_config,
            "recursion_depth": scan_config.get("recursion_depth"),
            "subdomain_scan": subdomain_scan,
            "banner_html": get_banner_html()
        }
        save_config(OUTPUT_DIR, selected_tools, wordlist, scan_config, scan_config.get("recursion_depth"), subdomain_scan)

        for fname in (SCANNED_DOMAINS, SCANNED_IPS):
            open(os.path.join(OUTPUT_DIR, fname), "a").close()

        # ---- PARALLEL SCANNING ----
        if selected_domains:
            print_status(f"Starting scan for {len(selected_domains)} domains using {MAX_THREADS} threads.")
            lock = threading.Lock()
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = [executor.submit(scan_domain, domain, config, lock) for domain in selected_domains]
                for future in as_completed(futures):
                    pass  # All output/logging handled in scan_domain
            print_success(f"Scan completed. Check {OUTPUT_DIR} for results.")
        else:
            print_status("No domains left to scan.")

    except Exception:
        print_error("Script terminated unexpectedly. Check error logs in output directory.")
        log_error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
