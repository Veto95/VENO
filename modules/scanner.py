import os
import subprocess
import time
import logging
from modules.scanner_steps import (
    subdomain_scan,  # Assuming you have this or want to add it
    extract_sensitive_files, 
    grep_juicy_info, 
    discover_parameters,
    sqlmap_on_vuln_urls, 
    advanced_xss_vuln_hunting, 
    generate_html_report
)

def run_subprocess(cmd, stdout_path=None, stderr_path=None, timeout=300):
    try:
        stdout = open(stdout_path, "w") if stdout_path else subprocess.DEVNULL
        stderr = open(stderr_path, "a") if stderr_path else subprocess.DEVNULL
        subprocess.run(cmd, stdout=stdout, stderr=stderr, timeout=timeout, check=True)
        if stdout is not subprocess.DEVNULL: stdout.close()
        if stderr is not subprocess.DEVNULL: stderr.close()
    except Exception as e:
        if stderr_path:
            with open(stderr_path, "a") as ferr:
                ferr.write(f"{' '.join(cmd)} failed: {e}\n")
        logging.error(f"Subprocess failed: {' '.join(cmd)} Exception: {e}")

def full_scan(domain, config):
    outdir = config["output_dir"]
    scan_cfg = config["scan_config"]
    wordlist = config["wordlist"]
    threads = scan_cfg.get("threads", 10)
    sqlmap_flags = scan_cfg.get("sqlmap_flags", "")
    selected_tools = config["selected_tools"]
    banner_html = config.get("banner_html", "")
    enable_subdomains = config.get("subdomains", False)

    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    os.makedirs(domain_dir, exist_ok=True)

    # 1. Subdomain scanning FIRST (if enabled)
    if enable_subdomains:
        try:
            subdomain_scan(domain, outdir)  # You must implement this if not present!
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"subdomain_scan failed: {e}\n")
        logging.info(f"[*] Subdomain scan completed for {domain}")

    # 2. waybackurls
    start = time.time()
    try:
        run_subprocess(
            ["waybackurls"],
            stdout_path=f"{domain_dir}/waybackurls.txt",
            stderr_path=error_log
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"waybackurls failed: {e}\n")
    logging.info(f"[*] waybackurls completed in {int(time.time()-start)}s")

    # 3. Sensitive files/juicy info with validation
    try:
        live_sensitive = extract_sensitive_files(domain, outdir)
        live_juicy = grep_juicy_info(domain, outdir)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"sensitive/juicy info extraction failed: {e}\n")
        logging.error(f"sensitive/juicy info extraction failed: {e}")

    # 4. Dynamic parameter discovery
    try:
        vuln_urls = discover_parameters(domain, outdir)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"parameter discovery failed: {e}\n")
        logging.error(f"parameter discovery failed: {e}")

    # 5. Targeted SQL injection testing
    try:
        sqlmap_on_vuln_urls(vuln_urls, outdir, domain)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"SQLMAP failed: {e}\n")
        logging.error(f"SQLMAP failed: {e}")

    # 6. Advanced XSS/vuln hunting
    try:
        advanced_xss_vuln_hunting(domain, outdir)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"XSS/vuln hunting failed: {e}\n")
        logging.error(f"XSS/vuln hunting failed: {e}")

    # 7. Generate HTML report (banner included)
    try:
        generate_html_report(domain, outdir, banner_html)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"HTML report generation failed: {e}\n")
        logging.error(f"HTML report generation failed: {e}")
