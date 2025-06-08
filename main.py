from modules.banner import banner
from modules.dependencies import check_dependencies
from modules.domain_input import get_domains
from modules.scanner import scan_domain
from pathlib import Path

OUTPUT_DIR = Path("output")

def main():
    banner()
    OUTPUT_DIR.mkdir(exist_ok=True)
    check_dependencies()

    print("[VENO] DOMAIN INPUT")
    domains = get_domains()

    for domain in domains:
        scan_domain(domain, OUTPUT_DIR)

    print("[✓] Scan completed. Check the output directory for results.")

if __name__ == "__main__":
    main()
