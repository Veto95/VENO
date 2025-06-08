import argparse
import logging

from modules.banner import banner, get_banner_html
from modules.domain_input import get_domains_interactive
from modules.scan_intensity import get_scan_intensity, suggest_tools
from modules.subdomain_scan import get_subdomain_scan_choice
from modules.wordlist import get_wordlist
from modules.config import save_config, load_config
from modules.scanner import full_scan

def main():
    banner()
    parser = argparse.ArgumentParser(description="VENO - Bug Bounty & Recon Tool")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    args = parser.parse_args()

    outdir = args.output
    domains = get_domains_interactive(outdir)
    scan_config = get_scan_intensity(outdir)
    subdomain_scan = get_subdomain_scan_choice(outdir)
    wordlist = get_wordlist(outdir)
    banner_html = get_banner_html()

    selected_tools = suggest_tools(scan_config, subdomain_scan)

    save_config(outdir, selected_tools, wordlist, scan_config, scan_config.get("recursion_depth", 1), subdomain_scan)

    for domain in domains:
        config = {
            "output_dir": outdir,
            "scan_config": scan_config,
            "subdomains": subdomain_scan,
            "banner_html": banner_html,
            "wordlist": wordlist,
            "selected_tools": selected_tools
        }
        full_scan(domain, config)

if __name__ == "__main__":
    main()
