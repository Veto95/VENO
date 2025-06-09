import os
import re
import subprocess
import time
import hashlib
import logging
from modules.dependencies import check_dependencies, dependencies

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

def print_step(msg):
    # Minimal output: just what the step is, nothing else
    if console:
        console.print(f"[cyan][VENO][/cyan] {msg}")
    else:
        print(color(f"[VENO] {msg}", "cyan"))

def step_check_dependencies(domain, config, context):
    print_step("Checking dependencies")
    check_dependencies(config.get("output_dir") or "output")

def step_subdomain_enum(domain, config, context):
    print_step("Enumerating subdomains")
    outdir = config.get("output_dir") or "output"
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    subfinder_out = os.path.join(domain_dir, "subfinder.txt")
    harvester_out = os.path.join(domain_dir, "theharvester.txt")
    all_subs_out = os.path.join(domain_dir, "all_subdomains.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    try:
        subprocess.run(
            ["subfinder", "-silent", "-d", domain, "-o", subfinder_out],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"subfinder failed: {e}\n")
    try:
        subprocess.run(
            ["theHarvester", "-d", domain, "-b", "all", "-f", harvester_out],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"theHarvester failed: {e}\n")
    subs = set()
    if os.path.isfile(subfinder_out):
        with open(subfinder_out) as f:
            for line in f:
                s = line.strip()
                if s: subs.add(s)
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
    with open(all_subs_out, "w") as f:
        for s in sorted(subs):
            f.write(f"{s}\n")
    context['subdomains'] = list(subs)
    # Probe for live subdomains with httprobe
    print_step("Probing live subdomains")
    live_subs = set()
    try:
        probe = subprocess.Popen(
            ["httprobe", "-c", "50"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
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
    live_out = os.path.join(domain_dir, "live_subdomains.txt")
    with open(live_out, "w") as f:
        for s in sorted(live_subs):
            f.write(f"{s}\n")
    context['live_subdomains'] = list(live_subs)

def step_wayback_urls(domain, config, context):
    print_step("Fetching wayback URLs")
    outdir = config.get("output_dir") or "output"
    wayback_file = f"{outdir}/{domain}/waybackurls.txt"
    error_log = f"{outdir}/{domain}/errors.log"
    try:
        with open(wayback_file, "w") as f:
            subprocess.run(["waybackurls", domain], stdout=f, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"waybackurls failed: {e}\n")
    context['waybackurls'] = wayback_file

def step_sensitive_file_enum(domain, config, context):
    print_step("Extracting sensitive files")
    outdir = config.get("output_dir") or "output"
    wayback_file = context.get('waybackurls', f"{outdir}/{domain}/waybackurls.txt")
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
                    is_live, has_sensitive = step_live_check(url, sensitive_keywords)
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
    context['sensitive_files'] = live_sensitive

def step_live_check(url, keywords=None):
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "8", url], capture_output=True, check=True, timeout=10)
        body = r.stdout.decode(errors="ignore")
        has_sensitive = any(kw in body.lower() for kw in (keywords or []))
        is_live = bool(body)
        return is_live, has_sensitive
    except Exception:
        return False, False

def step_juicy_info(domain, config, context):
    print_step("Extracting juicy info (secrets, keys, tokens, JS)")
    outdir = config.get("output_dir") or "output"
    wayback_file = context.get('waybackurls', f"{outdir}/{domain}/waybackurls.txt")
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
                    is_live, has_sensitive = step_live_check(url)
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
                        subprocess.run(["curl", "-s", "-m", "10", url, "-o", js_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
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
    context['juicy'] = live_juicy

def step_param_discovery(domain, config, context):
    print_step("Discovering dynamic parameters")
    outdir = config.get("output_dir") or "output"
    paramspider_out = f"{outdir}/{domain}/paramspider.txt"
    arjun_out = f"{outdir}/{domain}/arjun.txt"
    error_log = f"{outdir}/{domain}/errors.log"
    vulnerable_urls = []
    try:
        subprocess.run(
            ["paramspider", "-d", domain], 
            stdout=open(paramspider_out, "w"), 
            stderr=subprocess.DEVNULL, 
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
            stderr=subprocess.DEVNULL, check=True, timeout=300
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
    context['vuln_urls'] = vulnerable_urls

def step_advanced_xss(domain, config, context):
    print_step("Scanning for XSS and other vulnerabilities")
    outdir = config.get("output_dir") or "output"
    error_log = f"{outdir}/{domain}/errors.log"
    dalfox_out = f"{outdir}/{domain}/dalfox.txt"
    xsstrike_out = f"{outdir}/{domain}/xsstrike.txt"
    try:
        subprocess.run([
            "dalfox", "file", f"{outdir}/{domain}/paramspider.txt",
            "--custom-payload", "/usr/share/xss-payloads.txt",
            "--output", dalfox_out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"dalfox failed: {e}\n")
    try:
        subprocess.run([
            "xsstrike", "-l", f"{outdir}/{domain}/paramspider.txt",
            "-o", xsstrike_out
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"XSStrike failed: {e}\n")
    context['xss'] = dalfox_out

def step_dir_fuzz(domain, config, context):
    print_step("Directory and file fuzzing")
    outdir = config.get("output_dir") or "output"
    error_log = f"{outdir}/{domain}/errors.log"
    fuzz_results = []
    result_file = f"{outdir}/{domain}/dir_fuzz.txt"
    scan_config = context.get("scan_config", {})
    wordlist = context.get("wordlist") or "/usr/share/seclists/Discovery/Web-Content/common.txt"
    tool = scan_config.get("dir_fuzz_tool", "ffuf")
    threads = scan_config.get("threads", 10)

    if tool == "dirsearch":
        try:
            subprocess.run([
                "python3", "dirsearch/dirsearch.py", "-u", f"http://{domain}",
                "-w", wordlist,
                "--threads", str(threads),
                "-o", result_file,
                "--format", "plain"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.isfile(result_file):
                with open(result_file) as f:
                    for line in f:
                        m = re.match(r"\[.*\] (http[^\s]+)", line)
                        if m:
                            fuzz_results.append(m.group(1))
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"dirsearch failed: {e}\n")
    else:
        try:
            subprocess.run([
                "ffuf", "-u", f"http://{domain}/FUZZ",
                "-w", wordlist,
                "-t", str(threads),
                "-of", "csv",
                "-o", result_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.isfile(result_file):
                with open(result_file) as f:
                    for line in f:
                        if line.startswith("url"):
                            continue
                        parts = line.strip().split(",")
                        if len(parts) > 0 and parts[0].startswith("http"):
                            fuzz_results.append(parts[0])
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"ffuf failed: {e}\n")

    fuzz_results = sorted(set([x for x in fuzz_results if x]))
    with open(result_file, "a") as f:
        f.write("\n# Deduped Fuzz Results\n")
        for path in fuzz_results:
            f.write(path + "\n")
    context['dir_fuzz'] = fuzz_results

def step_sqlmap(domain, config, context):
    print_step("Running SQL injection tests")
    outdir = config.get("output_dir") or "output"
    vuln_urls = context.get('vuln_urls', [])
    error_log = f"{outdir}/{domain}/errors.log"
    sqlmap_logs = []
    for i, url in enumerate(vuln_urls):
        sqlmap_dir = f"{outdir}/{domain}/sqlmap_{i+1}"
        os.makedirs(sqlmap_dir, exist_ok=True)
        try:
            subprocess.run([
                "sqlmap", "-u", url, "--batch", f"--output-dir={sqlmap_dir}"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
            sqlmap_logs.append(sqlmap_dir)
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"sqlmap on {url} failed: {e}\n")
    context['sqlmap'] = sqlmap_logs

def step_nuclei_chain(domain, config, context):
    print_step("Running nuclei chain scan")
    outdir = config.get("output_dir") or "output"
    error_log = f"{outdir}/{domain}/errors.log"
    nuclei_targets = set()

    nuclei_targets.update(context.get('live_subdomains', []))
    nuclei_targets.update(context.get('dir_fuzz', []))
    nuclei_targets.update(context.get('juicy', []))
    nuclei_targets.update(context.get('sensitive_files', []))
    nuclei_targets.update(context.get('vuln_urls', []))
    nuclei_targets.update(context.get('waybackurls', []))

    agg_urls = []
    for u in nuclei_targets:
        if isinstance(u, str) and (u.startswith("http://") or u.startswith("https://")):
            agg_urls.append(u)
        elif isinstance(u, str):
            agg_urls.append(f"http://{u}")
            agg_urls.append(f"https://{u}")
        elif isinstance(u, list):
            for val in u:
                if val.startswith("http"):
                    agg_urls.append(val)
                else:
                    agg_urls.append(f"http://{val}")
                    agg_urls.append(f"https://{val}")

    agg_urls = sorted(set(agg_urls))
    nuclei_targets_file = f"{outdir}/{domain}/nuclei_targets.txt"
    with open(nuclei_targets_file, "w") as f:
        for url in agg_urls:
            f.write(url + "\n")

    nuclei_out = f"{outdir}/{domain}/nuclei_chained.txt"
    try:
        subprocess.run([
            "nuclei",
            "-l", nuclei_targets_file,
            "-o", nuclei_out,
            "-silent",
            "-c", str(context.get("scan_config", {}).get("threads", 10)),
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"Nuclei chained scan failed: {e}\n")
    context['nuclei_chained'] = nuclei_out

def step_report(domain, config, context):
    print_step("Generating HTML report")
    outdir = config.get("output_dir") or "output"
    html_report = f"{outdir}/{domain}/report.html"
    banner_html = "<pre>VENO BANNER HERE</pre>"
    with open(html_report, "w", encoding="utf-8") as fout:
        html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VENO Report - {domain}</title>
<style>
pre {{ white-space: pre-wrap; word-break: break-word; background: #f9f9f9; padding:1em; border-radius:8px; }}
</style>
</head>
<body>
{banner_html}
<h1>VENO Bug Bounty Report: {domain}</h1>
<div>
<b>Summary:</b>
<ul>
<li>Subdomains found: {len(context.get('subdomains', []))}</li>
<li>Live subdomains: {len(context.get('live_subdomains', []))}</li>
<li>Sensitive files: {len(context.get('sensitive_files', []))}</li>
<li>Juicy info: {len(context.get('juicy', []))}</li>
<li>Directory fuzzing: {len(context.get('dir_fuzz', []))}</li>
<li>Vulnerable URLs: {len(context.get('vuln_urls', []))}</li>
<li>Nuclei findings: {context.get('nuclei_chained', '')}</li>
</ul>
</div>
<!-- Expand this section to include more detailed results -->
</body></html>
"""
        fout.write(html_code)

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
