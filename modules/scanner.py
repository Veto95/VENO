import os
import re
import subprocess
import time
import hashlib
import logging
from modules.dependencies import check_dependencies

try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None

def color(text, clr):
    codes = {"green": "1;32", "red": "1;31", "yellow": "1;33", "cyan": "1;36", "magenta": "1;35", "bold": "1"}
    return f"\033[{codes.get(clr, '0')}m{text}\033[0m"

def timer_start():
    return time.time()

def timer_end(start, msg):
    elapsed = int(time.time() - start)
    msg = f"[VENO] {msg} completed in {elapsed}s"
    if console:
        console.print(f"[bold green]{msg}[/bold green]")
    else:
        print(color(msg, "green"))

def step_check_dependencies(domain, config, context):
    check_dependencies(config.get("output_dir") or "output")

def step_subdomain_enum(domain, config, context):
    # all logic is here
    subdomain_scan(domain, config.get("output_dir") or "output", context)

def step_wayback_urls(domain, config, context):
    wayback_urls(domain, config.get("output_dir") or "output", context)

def step_sensitive_file_enum(domain, config, context):
    extract_sensitive_files(domain, config.get("output_dir") or "output", context)

def step_juicy_info(domain, config, context):
    grep_juicy_info(domain, config.get("output_dir") or "output", context)

def step_param_discovery(domain, config, context):
    discover_parameters(domain, config.get("output_dir") or "output", context)

def step_advanced_xss(domain, config, context):
    advanced_xss_vuln_hunting(domain, config.get("output_dir") or "output", context)

def step_dir_fuzz(domain, config, context):
    directory_fuzzing(domain, config.get("output_dir") or "output", context)

def step_sqlmap(domain, config, context):
    sqlmap_on_vuln_urls(context.get('vuln_urls', []), config.get("output_dir") or "output", domain, context)

def step_nuclei_chain(domain, config, context):
    run_nuclei_chain(domain, config.get("output_dir") or "output", context)

def step_report(domain, config, context):
    banner_html = config.get("banner_html", "<pre>VENO BANNER HERE</pre>")
    generate_html_report(domain, config.get("output_dir") or "output", banner_html, context)

# --- You must import or define these logic functions above for this file to work:
# subdomain_scan, wayback_urls, extract_sensitive_files, grep_juicy_info, discover_parameters,
# advanced_xss_vuln_hunting, directory_fuzzing, sqlmap_on_vuln_urls, run_nuclei_chain, generate_html_report

# --- SCAN ORDER LIST ---
scanner_steps = [
    step_check_dependencies,
    step_subdomain_enum,
    step_wayback_urls,
    step_sensitive_file_enum,
    step_juicy_info,
    step_param_discovery,
    step_advanced_xss,
    step_dir_fuzz,
    step_sqlmap,
    step_nuclei_chain,
    step_report,
]
