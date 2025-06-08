import os
import re
import subprocess
import time
import hashlib
import logging

def timer_start():
    return time.time()

def timer_end(start, msg):
    elapsed = int(time.time() - start)
    logging.info(f"[VENO] {msg} completed in {elapsed}s")

# --- Subdomain scanning (full recursive logic) ---
def subdomain_scan(domain, outdir):
    logging.info(f"[VENO] Starting subdomain scan for {domain}")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    subfinder_out = os.path.join(domain_dir, "subfinder.txt")
    harvester_out = os.path.join(domain_dir, "theharvester.txt")
    all_subs_out = os.path.join(domain_dir, "all_subdomains.txt")
    live_out = os.path.join(domain_dir, "live_subdomains.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    # 1. Run subfinder
    try:
        subprocess.run(
            ["subfinder", "-silent", "-d", domain, "-o", subfinder_out],
            check=True, stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=180
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"subfinder failed: {e}\n")
    # 2. Run theHarvester
    try:
        subprocess.run(
            ["theHarvester", "-d", domain, "-b", "all", "-f", harvester_out],
            check=True, stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=180
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"theHarvester failed: {e}\n")

    # 3. Aggregate unique subdomains
    subs = set()
    # Parse subfinder
    if os.path.isfile(subfinder_out):
        with open(subfinder_out) as f:
            for line in f:
                s = line.strip()
                if s: subs.add(s)
    # Parse theHarvester HTML output
    if os.path.isfile(harvester_out):
        try:
            with open(harvester_out) as f:
                for line in f:
                    if domain in line and "." in line:
                        for token in line.split():
                            if domain in token and "." in token:
                                subs.add(token.strip('",[]()<>'))
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Parse theHarvester failed: {e}\n")
    # Write all subs to file
    with open(all_subs_out, "w") as f:
        for s in sorted(subs):
            f.write(f"{s}\n")
    logging.info(f"[VENO] Found {len(subs)} unique subdomains")

    # 4. Probe for live subdomains with httprobe (if installed)
    live_subs = set()
    try:
        probe = subprocess.Popen(
            ["httprobe", "-c", "50"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(error_log, "a"), text=True
        )
        with open(all_subs_out) as f:
            sublist = f.read()
            out, _ = probe.communicate(input=sublist, timeout=120)
            for line in out.splitlines():
                host = line.strip().replace('http://', '').replace('https://', '').split('/')[0]
                if host: live_subs.add(host)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"httprobe failed: {e}\n")
    # Write live subdomains
    with open(live_out, "w") as f:
        for s in sorted(live_subs):
            f.write(f"{s}\n")
    logging.info(f"[VENO] Found {len(live_subs)} live subdomains")

    # 5. Scan each live subdomain (recursive scan, disables further subdomain recursion)
    for sub in sorted(live_subs):
        if sub == domain: continue  # Skip root domain, already scanned
        logging.info(f"[VENO] Launching scan for subdomain: {sub}")
        try:
            from modules.scanner import full_scan
            from copy import deepcopy
            sub_config = deepcopy({
                "output_dir": outdir,
                "scan_config": {"threads": 5},
                "wordlist": "",
                "selected_tools": [],
                "banner_html": "",
                "subdomains": False  # Prevent infinite recursion
            })
            full_scan(sub, sub_config)
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Subdomain scan for {sub} failed: {e}\n")
            continue

    logging.info(f"[VENO] Subdomain scan completed for {domain}")

# --- Sensitive files/juicy info extraction ---
def extract_sensitive_files(domain, outdir):
    start = timer_start()
    wayback_file = f"{outdir}/{domain}/waybackurls.txt"
    sensitive_file = f"{outdir}/{domain}/sensitive_files.txt"
    error_log = f"{outdir}/{domain}/errors.log"
    live_sensitive = []
    sensitive_keywords = ["password", "key", "secret", "token", "aws", "credential"]
    sensitive_regex = "|".join(sensitive_keywords)
    if os.path.isfile(wayback_file):
        try:
            with open(wayback_file) as fin:
                urls = [line.strip() for line in fin if re.search(sensitive_regex, line, re.I)]
            with open(sensitive_file, "w") as fout:
                found = False
                for url in urls:
                    is_live, has_sensitive = live_check(url, sensitive_keywords)
                    if is_live:
                        found = True
                        mark = "[SENSITIVE]" if has_sensitive else "[LIVE]"
                        fout.write(f"{mark} {url}\n")
                        if has_sensitive:
                            live_sensitive.append(url)
                if found:
                    fout.write(f"\n# Sensitive Files and Links for {domain}\n")
                else:
                    fout.write("No sensitive files or links found.\n")
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Failed to extract sensitive files: {e}\n")
    timer_end(start, "Sensitive file extraction")
    return live_sensitive

def live_check(url, keywords=None):
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "8", url], capture_output=True, check=True, timeout=10)
        body = r.stdout.decode(errors="ignore")
        has_sensitive = any(kw in body.lower() for kw in (keywords or []))
        is_live = bool(body)
        return is_live, has_sensitive
    except Exception:
        return False, False

# --- Grep juicy info from URLs and JS files ---
def grep_juicy_info(domain, outdir):
    start = timer_start()
    wayback_file = f"{outdir}/{domain}/waybackurls.txt"
    juicy_file = f"{outdir}/{domain}/juicy_info.txt"
    js_dir = f"{outdir}/{domain}/js_files"
    error_log = f"{outdir}/{domain}/errors.log"
    os.makedirs(js_dir, exist_ok=True)
    live_juicy = []
    patterns = [
        r"api[_-]?key", r"token", r"password", r"secret", r"access[_-]?key", r"aws[_-]?key",
        r"aws[_-]?secret", r"auth[_-]?token", r"session[_-]?id", r"credential", r"stripe[_-]?key",
        r"s3\.amazonaws\.com", r"blob\.core\.windows\.net", r"firebaseio\.com", r"client[_-]?id",
        r"client[_-]?secret", r"oauth", r"db[_-]?password", r"database[_-]?url", r"[0-9a-f]{32,}",
        r"key=[a-zA-Z0-9_-]+", r"jwt=[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
        r"mongodb\+srv://", r"mysql://", r"postgres://", r"slack[_-]?token", r"bearer[_-]?token"
    ]
    false_positives = [
        "token_validation", "form_token", "csrf_token", "csrfmiddlewaretoken", "xsrf-token"
    ]
    pattern_regex = "|".join(patterns)
    found = False
    if os.path.isfile(wayback_file):
        try:
            with open(wayback_file) as fin:
                urls = [line.strip() for line in fin if re.search(pattern_regex, line, re.I)]
            with open(juicy_file, "w") as fout:
                for url in urls:
                    if any(fp in url for fp in false_positives):
                        continue
                    is_live, has_sensitive = live_check(url)
                    if is_live:
                        found = True
                        fout.write(f"[LIVE] {url}\n")
                        live_juicy.append(url)
                fin.seek(0)
                js_urls = [line.strip() for line in fin if line.lower().strip().endswith(".js")]
                for url in js_urls:
                    filename = hashlib.sha1(url.encode()).hexdigest() + ".js"
                    js_path = os.path.join(js_dir, filename)
                    try:
                        subprocess.run(["curl", "-s", "-m", "10", url, "-o", js_path], check=True)
                        if os.path.isfile(js_path):
                            with open(js_path) as jsf:
                                for jsline in jsf:
                                    if re.search(pattern_regex, jsline, re.I):
                                        if not any(fp in jsline for fp in false_positives):
                                            fout.write(f"[JS] {url}: {jsline}")
                                            found = True
                                            live_juicy.append(url)
                    except Exception as e:
                        with open(error_log, "a") as ferr:
                            ferr.write(f"Failed to fetch JS {url}: {e}\n")
                if found:
                    fout.write(f"\n# Juicy Info for {domain}\n")
                else:
                    fout.write("No juicy info found.\n")
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Failed to grep juicy info: {e}\n")
    timer_end(start, "Juicy info extraction")
    return live_juicy

# --- Dynamic parameter discovery ---
def discover_parameters(domain, outdir):
    logging.info(f"Discovering dynamic parameters for {domain}")
    start = timer_start()
    paramspider_out = f"{outdir}/{domain}/paramspider.txt"
    arjun_out = f"{outdir}/{domain}/arjun.txt"
    error_log = f"{outdir}/{domain}/errors.log"
    vulnerable_urls = []
    try:
        subprocess.run(
            ["paramspider", "-d", domain], 
            stdout=open(paramspider_out, "w"), 
            stderr=open(error_log, "a"), 
            check=True, timeout=300
        )
        urls = []
        with open(paramspider_out) as f:
            for line in f:
                if "http" in line and "=" in line:
                    urls.append(line.strip())
        with open("arjun_urls.txt", "w") as f:
            for url in urls:
                f.write(url + "\n")
        subprocess.run(
            ["arjun", "-i", "arjun_urls.txt", "-oT", arjun_out], 
            stderr=open(error_log, "a"), check=True, timeout=300
        )
        with open(arjun_out) as f:
            for line in f:
                if "GET" in line or "POST" in line:
                    match = re.search(r"(http[^\s]+)", line)
                    if match:
                        vulnerable_urls.append(match.group(1))
        os.remove("arjun_urls.txt")
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"Parameter discovery failed: {e}\n")
    timer_end(start, "Dynamic parameter discovery")
    return vulnerable_urls

# --- Advanced XSS/vuln hunting ---
def advanced_xss_vuln_hunting(domain, outdir):
    logging.info(f"Running advanced XSS and vulnerability hunting for {domain}")
    start = timer_start()
    error_log = f"{outdir}/{domain}/errors.log"
    dalfox_out = f"{outdir}/{domain}/dalfox.txt"
    xsstrike_out = f"{outdir}/{domain}/xsstrike.txt"
    nuclei_out = f"{outdir}/{domain}/nuclei.txt"
    try:
        subprocess.run([
            "dalfox", "file", f"{outdir}/{domain}/paramspider.txt",
            "--custom-payload", "/usr/share/xss-payloads.txt",
            "--output", dalfox_out
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=300)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"dalfox failed: {e}\n")
    try:
        subprocess.run([
            "xsstrike", "-l", f"{outdir}/{domain}/paramspider.txt",
            "-o", xsstrike_out
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=300)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"XSStrike failed: {e}\n")
    try:
        subprocess.run(["nuclei", "-update-templates"], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=120)
        subprocess.run([
            "nuclei", "-u", domain, "-o", nuclei_out
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=300)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"nuclei failed: {e}\n")
    timer_end(start, "Advanced XSS/vuln hunting")

# --- SQL Injection Testing ---
def sqlmap_on_vuln_urls(vuln_urls, outdir, domain):
    logging.info(f"Running sqlmap on discovered vulnerable URLs for {domain}")
    start = timer_start()
    error_log = f"{outdir}/{domain}/errors.log"
    for i, url in enumerate(vuln_urls):
        sqlmap_dir = f"{outdir}/{domain}/sqlmap_{i+1}"
        os.makedirs(sqlmap_dir, exist_ok=True)
        try:
            subprocess.run([
                "sqlmap", "-u", url, "--batch", f"--output-dir={sqlmap_dir}"
            ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"), timeout=300)
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"sqlmap on {url} failed: {e}\n")
    timer_end(start, "Targeted SQL injection testing")

# --- HTML Report Generation ---
def generate_html_report(domain, outdir, banner_html):
    html_report = f"{outdir}/{domain}/report.html"
    toc = "<li>Results</li>"  # Stub - you can extend this!
    with open(html_report, "w", encoding="utf-8") as fout:
        html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VENO Report - {domain}</title>
<style>
pre {{ white-space: pre-wrap; word-break: break-word; background: #f9f9f9; padding:1em; border-radius:8px; }}
</style>
<script>
function toggleSection(id) {{
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}}
window.onload = function() {{
    var first = document.querySelector('.section');
    if(first) first.classList.add('active');
}};
</script>
</head>
<body>
{banner_html}
<h1>VENO Bug Bounty Report: {domain}</h1>
<div id="toc">
<b>Table of Contents</b>
<ul>
{toc}
</ul>
</div>
<div style="margin-left:340px;">
<!-- Report content goes here. -->
</div>
</body></html>
"""
        fout.write(html_code)
    logging.info(f"Generated HTML report for {domain}")
