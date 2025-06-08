import os
from modules.banner import display_banner
from modules.dependencies import check_dependencies
from modules.domain_input import get_domains
from modules.config import save_config
from modules.scanner import scan_domain

OUTPUT_DIR = "output"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    display_banner()

    # Check dependencies
    check_dependencies(OUTPUT_DIR)

    # Domain input
    print("\n[VENO] DOMAIN INPUT")
    selected_domains = get_domains(OUTPUT_DIR)

    # Scan intensity configuration
    print("\n[VENO] SCAN INTENSITY")
    scan_config = input("Enter scan configuration (e.g., depth, threads, etc.): ")

    # Subdomain scan configuration
    print("\n[VENO] SUBDOMAIN SCAN")
    subdomain_scan = input("Enable subdomain scan? (yes/no): ")

    # Wordlist selection
    print("\n[VENO] WORDLIST SELECTION")
    wordlist = input("Enter path to wordlist: ")

    # Tool selection
    print("\n[VENO] TOOL SELECTION")
    selected_tools = input("Enter tools to run (comma-separated): ")

    # Save configuration
    save_config(OUTPUT_DIR, selected_tools, wordlist, scan_config, subdomain_scan)

    # Scan each domain
    for domain in selected_domains:
        try:
            scan_domain(domain, OUTPUT_DIR, scan_config, subdomain_scan, wordlist, selected_tools)
        except Exception as e:
            print(f"[!] Scan failed for {domain}. Error: {e}")

    print(f"[\u2713] Scan completed. Check {OUTPUT_DIR} for results.")

if __name__ == "__main__":
    main()
