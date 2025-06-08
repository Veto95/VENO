import os
import subprocess
import re
import hashlib
import time
import html
import requests

def timer_start():
    return time.time()

def timer_end(start_time, step_name="Step"):
    duration = int(time.time() - start_time)
    print(f"\033[1;34m[*] {step_name} completed in {duration}s\033[0m")

def live_check(url, keywords=None):
    """Return (is_live, contains_sensitive) for a URL."""
    try:
        resp = requests.get(url, timeout=8, verify=False, allow_redirects=True)
        if 200 <= resp.status_code < 400:
            if keywords:
                for word in keywords:
                    if word.lower() in resp.text.lower():
                        return True, True
            return True, False
        return False, False
    except Exception:
        return False, False

def extract_sensitive_files(domain, outdir):
    print(f"\033[1;36m[+] Extracting sensitive files and links for {domain}\033[0m")
    start = timer_start()
    wayback_file = f"{outdir}/{domain}/waybackurls.txt"
    sensitive_file = f"{outdir}/{domain}/sensitive_files.txt"
    error_log = f"{outdir}/{domain}/errors.log"
    live_sensitive = []

    sensitive_patterns = [
        r"\.env$", r"\.bak$", r"\.sql$", r"\.config$", r"\.conf$", r"\.json$",
        r"\.yaml$", r"\.yml$", r"\.log$", r"\.backup$", r"\.git/", r"\.svn/",
        r"phpinfo\.php$", r"admin", r"login", r"dashboard", r"wp-admin",
        r"wp-login\.php", r"config\.php", r"settings", r"backup"
    ]
    sensitive_regex = "|".join(sensitive_patterns)
    sensitive_keywords = ["password", "key", "secret", "token", "aws", "credential"]

    if os.path.isfile(wayback_file):
        try:
            with open(wayback_file) as fin:
                urls = [line.strip() for line in fin if re.search(sensitive_regex, line)]
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
                ferr.write(f"Failed to grep sensitive files: {e}\n")
    timer_end(start, "Sensitive file extraction")
    return live_sensitive

def grep_juicy_info(domain, outdir):
    print(f"\033[1;36m[+] Grepping juicy info from waybackurls and JS files for {domain}\033[0m")
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
                # Live JS files
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

def discover_parameters(domain, outdir):
    print(f"\033[1;36m[+] Discovering dynamic parameters for {domain}\033[0m")
    start = timer_start()
    paramspider_out = f"{outdir}/{domain}/paramspider.txt"
    arjun_out = f"{outdir}/{domain}/arjun.txt"
    error_log = f"{outdir}/{domain}/errors.log"
    vulnerable_urls = []
    # paramspider
    try:
        subprocess.run(["paramspider", "-d", domain], stdout=open(paramspider_out, "w"), stderr=open(error_log, "a"), check=True)
        urls = []
        with open(paramspider_out) as f:
            for line in f:
                if "http" in line and "=" in line:
                    urls.append(line.strip())
        # arjun
        with open("arjun_urls.txt", "w") as f:
            for url in urls:
                f.write(url + "\n")
        subprocess.run(["arjun", "-i", "arjun_urls.txt", "-oT", arjun_out], stderr=open(error_log, "a"), check=True)
        # Collect possible vulnerable URLs for sqlmap
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

def advanced_xss_vuln_hunting(domain, outdir):
    print(f"\033[1;36m[+] Running advanced XSS and vulnerability hunting for {domain}\033[0m")
    start = timer_start()
    error_log = f"{outdir}/{domain}/errors.log"
    dalfox_out = f"{outdir}/{domain}/dalfox.txt"
    xsstrike_out = f"{outdir}/{domain}/xsstrike.txt"
    nuclei_out = f"{outdir}/{domain}/nuclei.txt"
    # dalfox (XSS, with payloads)
    try:
        subprocess.run([
            "dalfox", "file", f"{outdir}/{domain}/paramspider.txt",
            "--custom-payload", "/usr/share/xss-payloads.txt",
            "--output", dalfox_out
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"dalfox failed: {e}\n")
    # XSStrike (XSS)
    try:
        subprocess.run([
            "xsstrike", "-l", f"{outdir}/{domain}/paramspider.txt",
            "-o", xsstrike_out
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"XSStrike failed: {e}\n")
    # nuclei (update, run)
    try:
        subprocess.run(["nuclei", "-update-templates"], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))
        subprocess.run([
            "nuclei", "-u", domain, "-o", nuclei_out
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"nuclei failed: {e}\n")
    timer_end(start, "Advanced XSS/vuln hunting")

def sqlmap_on_vuln_urls(vuln_urls, outdir, domain):
    print(f"\033[1;36m[+] Running sqlmap on discovered vulnerable URLs for {domain}\033[0m")
    start = timer_start()
    error_log = f"{outdir}/{domain}/errors.log"
    for i, url in enumerate(vuln_urls):
        sqlmap_dir = f"{outdir}/{domain}/sqlmap_{i+1}"
        os.makedirs(sqlmap_dir, exist_ok=True)
        try:
            subprocess.run([
                "sqlmap", "-u", url, "--batch", f"--output-dir={sqlmap_dir}"
            ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"sqlmap on {url} failed: {e}\n")
    timer_end(start, "Targeted SQL injection testing")

def generate_html_report(domain, outdir, banner_html=""):
    print(f"\033[1;36m[+] Generating interactive HTML report for {domain}\033[0m")
    start = time.time()
    domain_dir = f"{outdir}/{domain}"
    html_report = os.path.join(domain_dir, "report.html")
    files = [f for f in os.listdir(domain_dir) if os.path.isfile(os.path.join(domain_dir, f))]
    toc = ""
    body = ""
    for fname in files:
        if fname.endswith(".html") and fname != "report.html":
            continue
        section_id = fname.replace(".", "_")
        toc += f'<li><a href="#{section_id}" onclick="toggleSection(\'{section_id}\');return false;">{fname}</a></li>\n'
        raw_link = f'<a href="{fname}" target="_blank">[raw]</a>'
        with open(os.path.join(domain_dir, fname), encoding="utf-8", errors="ignore") as fin:
            content = html.escape(fin.read())
        body += f'''<div id="{section_id}" class="section">
<h2>{fname} {raw_link}</h2>
<pre>{content[:6000]}{"..." if len(content) > 6000 else ""}</pre>
</div>\n'''
    html_code = f"""<!DOCTYPE html>
<html><head>
<title>VENO Scan Report: {domain}</title>
<meta charset="utf-8"/>
<style>
body {{ font-family: Arial, sans-serif; background: #f7f7fa; color: #222; }}
h1 {{ color: #1e90ff; }}
#toc {{ background: #fff; border:1px solid #ccc; padding:1em; width:300px; float:left; margin-right:2em; }}
.section {{ display:none; margin-bottom:2em; background:#fff; border:1px solid #ccc; padding:1em; border-radius:8px; }}
.section.active {{ display:block; }}
a {{ color:#1e90ff; }}
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
{body}
</div>
</body></html>
"""
    with open(html_report, "w", encoding="utf-8") as fout:
        fout.write(html_code)
    print(f"\033[1;34m[*] HTML Report Generation completed in {int(time.time()-start)}s\033[0m")
