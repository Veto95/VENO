import os
import sys
import traceback
import warnings

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

OUTPUT_DIR = "output"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_scanned_domains():
    scanned_path = os.path.join(OUTPUT_DIR, "scanned_domains.txt")
    if os.path.exists(scanned_path):
        with open(scanned_path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def main():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        banner()
        print(f"\n\033[1;36m[VENO] OUTPUT DIRECTORY:\033[0m \033[1;33m{OUTPUT_DIR}\033[0m")
        print("\n\033[1;36m[VENO] DEPENDENCY CHECK\033[0m")
        check_dependencies(OUTPUT_DIR)

        clear_screen()
        banner()
        print(f"\n\033[1;36m[VENO] OUTPUT DIRECTORY:\033[0m \033[1;33m{OUTPUT_DIR}\033[0m")

        scanned_domains = get_scanned_domains()
        resume = False
        if scanned_domains:
            print("\n\033[1;36m[VENO] Existing scan detected.\033[0m")
            resp = input("Do you want to resume the last scan? [Y/n]: ").strip().lower()
            if resp in ("", "y", "yes"):
                resume = True

        print("\n\033[1;36m[VENO] DOMAIN INPUT\033[0m")
        selected_domains = get_domains(OUTPUT_DIR)

        if resume:
            selected_domains = [d for d in selected_domains if d not in scanned_domains]
            print(f"\033[1;36m[VENO] Resuming scan for remaining {len(selected_domains)} domains...\033[0m")
        else:
            open(f"{OUTPUT_DIR}/scanned_domains.txt", "w").close()
            open(f"{OUTPUT_DIR}/scanned_ips.txt", "w").close()

        print(f"\n\033[1;36m[VENO] OUTPUT DIRECTORY:\033[0m \033[1;33m{OUTPUT_DIR}\033[0m")
        print("\n\033[1;36m[VENO] SCAN INTENSITY\033[0m")
        scan_config = get_scan_intensity(OUTPUT_DIR)

        print(f"\n\033[1;36m[VENO] OUTPUT DIRECTORY:\033[0m \033[1;33m{OUTPUT_DIR}\033[0m")
        print("\n\033[1;36m[VENO] SUBDOMAIN SCAN\033[0m")
        subdomain_scan = get_subdomain_scan_choice(OUTPUT_DIR)

        print(f"\n\033[1;36m[VENO] OUTPUT DIRECTORY:\033[0m \033[1;33m{OUTPUT_DIR}\033[0m")
        print("\n\033[1;36m[VENO] WORDLIST SELECTION\033[0m")
        wordlist = get_wordlist(OUTPUT_DIR)

        selected_tools = suggest_tools(scan_config, subdomain_scan)
        print(f"\n\033[1;36m[VENO] TOOL SELECTION (auto):\033[0m \033[1;32m{', '.join(selected_tools)}\033[0m")

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

        for i, domain in enumerate(selected_domains, 1):
            print(f"\n\033[1;33m[VENO] Scanning {i}/{len(selected_domains)}: {domain}\033[0m")
            try:
                full_scan(domain, config)
                with open(f"{OUTPUT_DIR}/scanned_domains.txt", "a") as f:
                    f.write(domain + "\n")
            except Exception:
                print(f"\033[1;31m[!] Scan failed for {domain}. See {OUTPUT_DIR}/{domain}/errors.log for details.\033[0m")

        print(f"\n\033[1;32m[\u2713] Scan completed. Check {OUTPUT_DIR} for results.\033[0m")
    except Exception:
        print(f"\033[1;31m[!] Script terminated unexpectedly. Check error logs in output directory.\033[0m")
        with open(f"{OUTPUT_DIR}/error.log", "a") as f:
            f.write(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
