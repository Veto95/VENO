import argparse
import logging
import os
import sys
from modules.banner import print_banner
from modules.domain_input import (
    get_domains,
    load_domains,
    clean_domain,
    validate_domain
)
from modules.config import get_config
from modules.scanner import full_scan

try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None

def color(text, clr):
    codes = {"green": "1;32", "red": "1;31", "yellow": "1;33", "cyan": "1;36", "magenta": "1;35", "bold": "1"}
    return f"\033[{codes.get(clr, '0')}m{text}\033[0m"

def clear_screen():
    # Cross-platform screen clear
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def get_valid_domains_from_arg(domains_arg, outdir):
    # If file, load and validate
    if os.path.isfile(domains_arg):
        return load_domains(domains_arg, outdir)
    # Else, treat as comma/space separated manual input
    raw_domains = [clean_domain(d) for d in domains_arg.replace(',', ' ').split() if d.strip()]
    valid_domains = [d for d in raw_domains if validate_domain(d)]
    if not valid_domains:
        msg = "[VENO] No valid domains supplied in argument."
        if console:
            console.print(f"[bold red]{msg}[/bold red]")
        else:
            print(color(msg, "red"))
        sys.exit(1)
    return valid_domains

def main():
    print_banner(console=console, plain_fallback=color)

    parser = argparse.ArgumentParser(description="VENO Automated Bug Bounty Scanner [DEUS ACTIVE MODE]")
    parser.add_argument("--intensity", choices=["low", "medium", "high", "max"], default="medium", help="Scan intensity")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--domains", help="Comma/space separated domains or path to file (overrides interactive prompt)")
    args = parser.parse_args()

    outdir = args.output.strip()
    scan_intensity = args.intensity

    # Get domains (from env, CLI, file, or interactive)
    if args.domains:
        domains = get_valid_domains_from_arg(args.domains.strip(), outdir)
    else:
        domains = get_domains(outdir)

    if not domains:
        msg = "[VENO] No valid domains supplied. Exiting."
        if console:
            console.print(f"[bold red]{msg}[/bold red]")
        else:
            print(color(msg, "red"))
        sys.exit(1)

    configs = []
    for domain in domains:
        config = get_config(domain=domain, output_dir=outdir, scan_intensity=scan_intensity)
        configs.append((domain, config))

    # Clear screen and show only the banner before scanning
    clear_screen()
    print_banner(console=console, plain_fallback=color)

    for domain, config in configs:
        domain_dir = os.path.join(outdir, domain)
        os.makedirs(domain_dir, exist_ok=True)
        log_file = os.path.join(domain_dir, "veno.log")
        logger = logging.getLogger(domain)
        logger.setLevel(logging.INFO)
        # Remove previous handlers
        if logger.hasHandlers():
            logger.handlers.clear()
        handler = logging.FileHandler(log_file, mode="w")
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Run full scan
        results = full_scan(domain, config)
        msg = f"[VENO] Scan complete for {domain}! See {outdir}/{domain}/report.html"
        if console:
            console.print(f"[bold green]{msg}[/bold green]")
        else:
            print(color(msg, "green"))

if __name__ == "__main__":
    main()
