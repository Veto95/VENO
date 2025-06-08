import logging

# Import all scan step functions from scanner_steps
from modules.scanner_steps import (
    subdomain_scan,
    extract_sensitive_files,
    grep_juicy_info,
    discover_parameters,
    advanced_xss_vuln_hunting,
    sqlmap_on_vuln_urls,
    generate_html_report
)

def full_scan(domain, config):
    """
    Orchestrates the full scan workflow for a given domain.
    config: dict with at least 'output_dir', 'scan_config', 'subdomains', 'banner_html'
    """
    logging.info(f"[VENO] Starting full scan for {domain}")

    outdir = config.get("output_dir", "output")
    subdomains_enabled = config.get("subdomains", True)
    banner_html = config.get("banner_html", "")
    threads = config.get("scan_config", {}).get("threads", 5)
    wordlist = config.get("wordlist", "")

    # 1. Subdomain scan (recursive, unless disabled)
    if subdomains_enabled:
        try:
            subdomain_scan(domain, outdir)
        except Exception as e:
            logging.error(f"[VENO] Subdomain scan failed for {domain}: {e}")

    # 2. Sensitive files extraction
    try:
        extract_sensitive_files(domain, outdir)
    except Exception as e:
        logging.error(f"[VENO] Sensitive file extraction failed for {domain}: {e}")

    # 3. Grep juicy info (URLs/JS)
    try:
        grep_juicy_info(domain, outdir)
    except Exception as e:
        logging.error(f"[VENO] Juicy info grep failed for {domain}: {e}")

    # 4. Discover parameters
    vuln_urls = []
    try:
        vuln_urls = discover_parameters(domain, outdir)
    except Exception as e:
        logging.error(f"[VENO] Parameter discovery failed for {domain}: {e}")

    # 5. Advanced XSS/vuln hunting
    try:
        advanced_xss_vuln_hunting(domain, outdir)
    except Exception as e:
        logging.error(f"[VENO] Advanced vuln hunting failed for {domain}: {e}")

    # 6. SQL Injection testing
    if vuln_urls:
        try:
            sqlmap_on_vuln_urls(vuln_urls, outdir, domain)
        except Exception as e:
            logging.error(f"[VENO] SQLmap failed for {domain}: {e}")

    # 7. HTML Report
    try:
        generate_html_report(domain, outdir, banner_html)
    except Exception as e:
        logging.error(f"[VENO] HTML report generation failed for {domain}: {e}")

    logging.info(f"[VENO] Full scan completed for {domain}")
