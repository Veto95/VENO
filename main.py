import os
import sys
import traceback
from modules.banner import banner
from modules.dependencies import check_dependencies
from modules.domain_input import get_domains
from modules.scan_intensity import get_scan_intensity, suggest_tools
from modules.subdomain_scan import get_subdomain_scan_choice
from modules.wordlist import get_wordlist
from modules.config import save_config
from modules.scanner import scan_domain

OUTPUT_DIR = "output"

def main():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        banner()

        check_dependencies(OUTPUT_DIR)

        print("\n\033[1;36m[VENO] DOMAIN INPUT\033[0m")
        selected_domains = get_domains(OUTPUT_DIR)

        print("\n\033[1;36m[VENO] SCAN INTENSITY\033[0m")
        scan_config = get_scan_intensity(OUTPUT_DIR)

        print("\n\033[1;36m[VENO] SUBDOMAIN SCAN\033[0m")
        subdomain_scan = get_subdomain_scan_choice(OUTPUT_DIR)

        print("\n\033[1;36m[VENO] WORDLIST SELECTION\033[0m")
        wordlist = get_wordlist(OUTPUT_DIR)

        # Automatic tool selection
        selected_tools = suggest_tools(scan_config, subdomain_scan)
        print(f"\n\033[1;36m[VENO] TOOL SELECTION (auto):\033[0m \033[1;32m{', '.join(selected_tools)}\033[0m")

        save_config(
            OUTPUT_DIR, selected_tools, wordlist, scan_config,
            scan_config.get("recursion_depth"), subdomain_scan
        )

        open(f"{OUTPUT_DIR}/scanned_domains.txt", "a").close()
        open(f"{OUTPUT_DIR}/scanned_ips.txt", "a").close()

        for i, domain in enumerate(selected_domains, 1):
            print(f"\n\033[1;33m[VENO] Scanning {i}/{len(selected_domains)}: {domain}\033[0m")
            try:
                scan_domain(
                    domain, OUTPUT_DIR,
                    scan_config.get("threads"),
                    scan_config.get("hak_depth"),
                    scan_config.get("sqlmap_flags"),
                    wordlist, selected_tools,
                    scan_config.get("recursion_depth"), subdomain_scan
                )
            except Exception as e:
                print(f"\033[1;31m[!] Scan failed for {domain}. See {OUTPUT_DIR}/{domain}/errors.log for details.\033[0m")

        print(f"\n\033[1;32m[\u2713] Scan completed. Check {OUTPUT_DIR} for results.\033[0m")
    except Exception as e:
        print(f"\033[1;31m[!] Script terminated unexpectedly. Check error logs in output directory.\033[0m")
        with open(f"{OUTPUT_DIR}/error.log", "a") as f:
            f.write(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
