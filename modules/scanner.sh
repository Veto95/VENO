from modules.scanner_steps import (
    extract_sensitive_files, grep_juicy_info, discover_parameters,
    sqlmap_on_vuln_urls, advanced_xss_vuln_hunting, generate_html_report
)
import os
import subprocess
import time

def full_scan(domain, config):
    outdir = config["output_dir"]
    scan_cfg = config["scan_config"]
    wordlist = config["wordlist"]
    threads = scan_cfg.get("threads", 10)
    sqlmap_flags = scan_cfg.get("sqlmap_flags", "")
    selected_tools = config["selected_tools"]
    banner_html = config.get("banner_html", "")

    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    os.makedirs(domain_dir, exist_ok=True)

    # 1. waybackurls
    start = time.time()
    try:
        subprocess.run(
            ["waybackurls"], input=f"{domain}\n".encode(),
            stdout=open(f"{domain_dir}/waybackurls.txt", "w"),
            stderr=open(error_log, "a"), check=True
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"waybackurls failed: {e}\n")
    print(f"\033[1;34m[*] waybackurls completed in {int(time.time()-start)}s\033[0m")

    # 2. Sensitive files/juicy info with validation
    live_sensitive = extract_sensitive_files(domain, outdir)
    live_juicy = grep_juicy_info(domain, outdir)

    # 3. Dynamic parameter discovery
    vuln_urls = discover_parameters(domain, outdir)
    # 4. Targeted SQL injection testing
    sqlmap_on_vuln_urls(vuln_urls, outdir, domain)
    # 5. Advanced XSS/vuln hunting
    advanced_xss_vuln_hunting(domain, outdir)
    # 6. Add other tools as needed...
    # 7. Interactive HTML report (banner included)
    generate_html_report(domain, outdir, banner_html)
