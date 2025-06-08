import logging
from modules.scanner_steps import (
    subdomain_scan,
    extract_sensitive_files,
    grep_juicy_info,
    discover_parameters,
    advanced_xss_vuln_hunting,
    sqlmap_on_vuln_urls,
    generate_html_report,
    chain_vulnerabilities
)

try:
    from rich.progress import Progress
except ImportError:
    Progress = None

def full_scan(domain, config):
    logging.info(f"[VENO] Starting full scan for {domain}")
    outdir = config.get("output_dir", "output")
    subdomains_enabled = config.get("subdomains", True)
    banner_html = config.get("banner_html", "")
    threads = config.get("scan_config", {}).get("threads", 5)
    wordlist = config.get("wordlist", "")
    context = {}

    steps = [
        ("Subdomain Scan", lambda: subdomain_scan(domain, outdir, context) if subdomains_enabled else None),
        ("Sensitive Files Extraction", lambda: extract_sensitive_files(domain, outdir, context)),
        ("Grep Juicy Info", lambda: grep_juicy_info(domain, outdir, context)),
        ("Discover Parameters", lambda: discover_parameters(domain, outdir, context)),
        ("Advanced XSS/Vuln Hunting", lambda: advanced_xss_vuln_hunting(domain, outdir, context)),
        ("SQL Injection Testing", lambda: sqlmap_on_vuln_urls(context.get('vuln_urls', []), outdir, domain, context)),
        ("HTML Report", lambda: generate_html_report(domain, outdir, banner_html, context)),
    ]

    if Progress:
        with Progress() as progress:
            task = progress.add_task(f"[yellow]Scanning {domain}", total=len(steps))
            for step_name, step_func in steps:
                progress.console.print(f"[magenta]{step_name}[/magenta]")
                step_func()
                progress.update(task, advance=1)
    else:
        for step_name, step_func in steps:
            print(f"[VENO] {step_name}")
            step_func()

    # Vulnerability chaining summary
    chains = chain_vulnerabilities(context)
    if chains:
        msg = f"[VENO] Potential vulnerability chains discovered:"
        print(f"\033[1;31m{msg}\033[0m")
        for sub, vul in chains:
            print(f"  [CHAIN] {sub} → {vul}")

    logging.info(f"[VENO] Full scan completed for {domain}")
