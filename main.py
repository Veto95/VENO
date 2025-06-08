import argparse
import os
import sys
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.banner import banner, get_banner_html
from modules.dependencies import check_dependencies
from modules.domain_input import get_domains, load_domains
from modules.scan_intensity import get_scan_intensity, suggest_tools
from modules.subdomain_scan import get_subdomain_scan_choice
from modules.wordlist import get_wordlist
from modules.config import save_config
from modules.scanner import full_scan

OUTPUT_DIR = "output"
SCANNED_DOMAINS = "scanned_domains.txt"
ERROR_LOG = "error.log"

def setup_logging(output_dir):
    log_path = os.path.join(output_dir, ERROR_LOG)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

def parse_args():
    parser = argparse.ArgumentParser(description="VENO - Bug Bounty & Recon Tool")
    parser.add_argument('--domains', help='Path to domain file or comma-separated list', required=False)
    parser.add_argument('--wordlist', help='Path to wordlist', required=False)
    parser.add_argument('--intensity', choices=['fast', 'normal', 'deep'], default='normal')
    parser.add_argument('--output-dir', default=OUTPUT_DIR)
    parser.add_argument('--subdomains', action='store_true', help='Enable subdomain scan')
    parser.add_argument('--resume', action='store_true', help='Resume last scan')
    parser.add_argument('--max-threads', type=int, default=5)
    return parser.parse_args()

def read_domains(domains_arg, outdir):
    if not domains_arg:
        return get_domains(outdir)
    if os.path.isfile(domains_arg):
        return load_domains(domains_arg, outdir)
    # comma or space separated
    domain_list = [d.strip() for d in domains_arg.replace(',', ' ').split() if d.strip()]
    if not domain_list:
        raise ValueError("No valid domains provided.")
    return domain_list

def get_scanned_domains(output_dir):
    scanned_path = os.path.join(output_dir, SCANNED_DOMAINS)
    if os.path.exists(scanned_path):
        with open(scanned_path, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def log_error(message, domain=None, output_dir=OUTPUT_DIR):
    if domain:
        dir_path = os.path.join(output_dir, domain)
        os.makedirs(dir_path, exist_ok=True)
        err_path = os.path.join(dir_path, "errors.log")
    else:
        err_path = os.path.join(output_dir, ERROR_LOG)
    with open(err_path, "a") as f:
        f.write(message + "\n")
    logging.error(message)

def scan_domain(domain, config, lock, output_dir):
    try:
        logging.info(f"Scanning: {domain}")
        full_scan(domain, config)
        with lock:
            with open(os.path.join(output_dir, SCANNED_DOMAINS), "a") as f:
                f.write(domain + "\n")
    except Exception as e:
        logging.error(f"Scan failed for {domain}.")
        traceback_str = traceback.format_exc()
        log_error(traceback_str, domain=domain, output_dir=output_dir)

def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    setup_logging(args.output_dir)
    banner()
    logging.info(f"OUTPUT DIRECTORY: {args.output_dir}")

    check_dependencies(args.output_dir)

    try:
        domains = read_domains(args.domains, args.output_dir)
    except Exception as e:
        logging.error(f"Failed to read domains: {e}")
        sys.exit(1)

    # ---- WORDLIST SELECTION: THIS IS WHERE THE CYBERPUNK MAGIC HAPPENS ----
    if not args.wordlist:
        wordlist = get_wordlist(args.output_dir)
    else:
        wordlist = args.wordlist
        if not os.path.isfile(wordlist):
            print("\033[1;31m[!] Wordlist not found: {}\033[0m".format(wordlist))
            logging.error(f"Wordlist not found: {wordlist}")
            sys.exit(1)

    scan_config = {
        "intensity": args.intensity,
        "threads": args.max_threads,
        "sqlmap_flags": "",
    }

    selected_tools = suggest_tools(args.intensity)
    banner_html = get_banner_html()

    config = {
        "output_dir": args.output_dir,
        "scan_config": scan_config,
        "wordlist": wordlist,
        "selected_tools": selected_tools,
        "banner_html": banner_html,
        "subdomains": args.subdomains,
    }

    from threading import Lock
    lock = Lock()
    scanned_domains = get_scanned_domains(args.output_dir)

    if args.resume:
        domains_to_scan = [d for d in domains if d not in scanned_domains]
    else:
        domains_to_scan = domains

    if not domains_to_scan:
        print("\033[1;33m[!] No new domains to scan.\033[0m")
        logging.info("No new domains to scan.")
        sys.exit(0)

    with ThreadPoolExecutor(max_workers=args.max_threads) as executor:
        futures = [executor.submit(scan_domain, domain, config, lock, args.output_dir) for domain in domains_to_scan]
        for future in as_completed(futures):
            pass  # All logging handled internally

if __name__ == "__main__":
    main()
