import os
import re
import subprocess
import time
import hashlib
import logging
import random
import requests
from modules.reporter import generate_report
from modules.dependencies import check_dependencies, dependencies
from urllib.parse import urlparse

try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
    logger.info(msg)

def print_step(msg):
    if console:
        console.print(f"[cyan][VENO][/cyan] {msg}")
    else:
        print(color(f"[VENO] {msg}", "cyan"))
    logger.info(msg)

def print_found(step, count):
    print_step(f"{step} - Found {count}")

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "curl/8.0.1",
    ]
    return random.choice(user_agents)

def get_proxy():
    proxies = [
        # Add your proxies here if needed like {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
    ]
    return random.choice(proxies) if proxies else None

def random_delay(intensity):
    # Intensity: light=0.2-0.6, medium=0.6-1.5, heavy=1-3
    if intensity == "light":
        time.sleep(random.uniform(0.2, 0.6))
    elif intensity == "medium":
        time.sleep(random.uniform(0.6, 1.5))
    else:
        time.sleep(random.uniform(1, 3))

def step_check_dependencies(domain, config, context):
    print_step("Checking dependencies")
    outdir = config.get("output_dir") or "output"
    os.makedirs(outdir, exist_ok=True)
    error_log = os.path.join(outdir, f"{domain}/errors.log")
    try:
        check_dependencies(outdir)
        context['dependencies'] = True
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"Dependency check failed: {e}\n")
        logger.error(f"Dependency check failed: {e}")
        raise SystemExit(f"Dependency check failed: {e}")

def step_subdomain_enum(domain, config, context):
    print_step("Enumerating subdomains")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    subfinder_out = os.path.join(domain_dir, "subfinder.txt")
    harvester_out = os.path.join(domain_dir, "theharvester.xml")
    all_subs_out = os.path.join(domain_dir, "all_subdomains.txt")
    live_out = os.path.join(domain_dir, "live_subdomains.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    # Subfinder
    try:
        random_delay(intensity)
        subprocess.run(
            ["subfinder", "-silent", "-d", domain, "-o", subfinder_out, "-t", "10", "-timeout", "5"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180
        )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"subfinder failed: {e}\n")
        logger.error(f"subfinder failed: {e}")
    # theHarvester
    try:
        random_delay(intensity)
        proxy = get_proxy()
        cmd = ["theHarvester", "-d", domain, "-b", "all", "-f", harvester_out]
        if proxy:
            cmd.extend(["--proxy", proxy.get("http")])
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"theHarvester failed: {e}\n")
        logger.error(f"theHarvester failed: {e}")
    # Combine subdomains
    subs = set()
    if os.path.isfile(subfinder_out):
        with open(subfinder_out) as f:
            subs.update(line.strip() for line in f if line.strip())
    if os.path.isfile(harvester_out):
        try:
            with open(harvester_out) as f:
                content = f.read()
                for token in re.findall(rf"[\w\-\.]+{re.escape(domain)}", content):
                    subs.add(token.strip('",[]()<>'))
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Parse theHarvester failed: {e}\n")
            logger.error(f"Parse theHarvester failed: {e}")
    with open(all_subs_out, "w") as f:
        for s in sorted(subs):
            f.write(f"{s}\n")
    context['subdomains'] = list(subs)
    print_found("Subdomains", len(subs))
    # Probe live subdomains with httprobe
    print_step("Probing live subdomains")
    live_subs = set()
    try:
        probe = subprocess.Popen(
            ["httprobe", "-c", "50", "-t", "5000", "-p", "http:80,https:443"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        with open(all_subs_out) as f:
            out, _ = probe.communicate(input=f.read(), timeout=120)
            for line in out.splitlines():
                host = line.strip().replace('http://', '').replace('https://', '').split('/')[0]
                if host:
                    live_subs.add(host)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"httprobe failed: {e}\n")
        logger.error(f"httprobe failed: {e}")
    with open(live_out, "w") as f:
        for s in sorted(live_subs):
            f.write(f"{s}\n")
    context['live_subdomains'] = list(live_subs)
    print_found("Live subdomains", len(live_subs))
    timer_end(start, "Subdomain enumeration")

def step_wayback_urls(domain, config, context):
    print_step("Fetching wayback URLs")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    wayback_file = os.path.join(outdir, domain, "waybackurls.txt")
    error_log = os.path.join(outdir, domain, "errors.log")
    try:
        random_delay(intensity)
        with open(wayback_file, "w") as f:
            subprocess.run(
                ["waybackurls", domain],
                stdout=f, stderr=subprocess.DEVNULL, check=True, timeout=120
            )
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"waybackurls failed: {e}\n")
        logger.error(f"waybackurls failed: {e}")
    context['waybackurls'] = wayback_file
    count = 0
    if os.path.isfile(wayback_file):
        with open(wayback_file) as f:
            count = sum(1 for _ in f)
    print_found("Wayback URLs", count)
    timer_end(start, "Wayback URLs fetching")

def step_sensitive_file_enum(domain, config, context):
    print_step("Extracting sensitive files")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    wayback_file = context.get('waybackurls', os.path.join(outdir, domain, "waybackurls.txt"))
    sensitive_file = os.path.join(outdir, domain, "sensitive_files.txt")
    error_log = os.path.join(outdir, domain, "errors.log")
    live_sensitive = []
    sensitive_patterns = [
        r"\.env$", r"\.bak$", r"\.sql$", r"\.config$", r"\.conf$", r"\.json$", r"\.yaml$", r"\.yml$",
        r"\.log$", r"\.backup$", r"\.git/", r"\.svn/", r"\.htaccess$", r"\.htpasswd$",
        r"phpinfo\.php$", r"wp-config\.php$", r"config\.php$", r"settings\.php$", r"database\.php$",
        r"admin", r"login", r"dashboard", r"wp-admin", r"wp-login\.php$", r"backup",
        r"api_key", r"secret_key", r"access_token", r"auth_token", r"password", r"credential",
        r"aws_access_key", r"aws_secret_key", r"s3\.amazonaws\.com", r"firebaseio\.com",
        r"private_key", r"ssh_key", r"\.pem$", r"\.key$", r"\.cer$", r"\.crt$",
        r"web\.config$", r"app\.config$", r"connectionStrings", r"debug", r"test", r"staging",
        r"\.swp$", r"\.old$", r"\.tmp$", r"\.save$", r"~"
    ]
    sensitive_regex = "|".join(sensitive_patterns)
    sensitive_keywords = [
        "password", "key", "secret", "token", "aws", "credential", "api", "auth",
        "access", "private", "admin", "root", "user", "pass", "login", "database",
        "connection", "config", "settings"
    ]
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
                    random_delay(intensity)
                if found:
                    fout.write(f"\n# Sensitive Files and Links for {domain}\n")
                else:
                    fout.write("No sensitive files or links found.\n")
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Failed to extract sensitive files: {e}\n")
            logger.error(f"Failed to extract sensitive files: {e}")
    context['sensitive_files'] = live_sensitive
    print_found("Sensitive files/URLs", len(live_sensitive))
    timer_end(start, "Sensitive file enumeration")

def step_live_check(url, keywords=None):
    try:
        headers = {"User-Agent": get_random_user_agent()}
        proxy = get_proxy()
        r = requests.get(
            url, headers=headers, proxies=proxy, timeout=8, allow_redirects=True,
            verify=False
        )
        body = r.text.lower()
        has_sensitive = any(kw in body for kw in (keywords or []))
        is_live = r.status_code in [200, 301, 302]
        return is_live, has_sensitive
    except Exception:
        return False, False

def step_juicy_info(domain, config, context):
    print_step("Extracting juicy info (secrets, keys, tokens, JS)")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    wayback_file = context.get('waybackurls', os.path.join(outdir, domain, "waybackurls.txt"))
    juicy_file = os.path.join(outdir, domain, "juicy_info.txt")
    js_dir = os.path.join(outdir, domain, "js_files")
    os.makedirs(js_dir, exist_ok=True)
    error_log = os.path.join(outdir, domain, "errors.log")
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
        "csrf_token", "xsrf_token", "sessionid", "nonce", "token_validation", "form_token"
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
                    random_delay(intensity)
                fin.seek(0)
                js_urls = [line.strip() for line in fin if line.lower().strip().endswith(".js")]
                for url in js_urls:
                    filename = hashlib.sha1(url.encode()).hexdigest() + ".js"
                    js_path = os.path.join(js_dir, filename)
                    try:
                        headers = {"User-Agent": get_random_user_agent()}
                        proxy = get_proxy()
                        r = requests.get(
                            url, headers=headers, proxies=proxy, timeout=10, verify=False
                        )
                        with open(js_path, "w") as jsf:
                            jsf.write(r.text)
                        with open(js_path) as jsf:
                            for jsline in jsf:
                                if re.search(pattern_regex, jsline, re.I) and not any(fp in jsline for fp in false_positives):
                                    fout.write(f"[JS] {url}: {jsline}")
                                    found = True
                                    live_juicy.append(url)
                        random_delay(intensity)
                    except Exception as e:
                        with open(error_log, "a") as ferr:
                            ferr.write(f"Failed to fetch JS {url}: {e}\n")
                        logger.error(f"Failed to fetch JS {url}: {e}")
                if found:
                    fout.write(f"\n# Juicy Info for {domain}\n")
                else:
                    fout.write("No juicy info found.\n")
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Failed to grep juicy info: {e}\n")
            logger.error(f"Failed to grep juicy info: {e}")
    context['juicy'] = live_juicy
    print_found("Juicy info (URLs)", len(live_juicy))
    timer_end(start, "Juicy info extraction")

def step_param_discovery(domain, config, context):
    print_step("Discovering dynamic parameters")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    paramspider_out = os.path.join(outdir, domain, "paramspider.txt")
    arjun_out = os.path.join(outdir, domain, "arjun.txt")
    error_log = os.path.join(outdir, domain, "errors.log")
    vulnerable_urls = []
    try:
        subprocess.run(
            ["paramspider", "-d", domain, "-o", paramspider_out, "--timeout", "5", "--delay", "0.5"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=300
        )
        random_delay(intensity)
        urls = []
        if os.path.isfile(paramspider_out):
            with open(paramspider_out) as f:
                for line in f:
                    if "http" in line and "=" in line:
                        urls.append(line.strip())
        with open("arjun_urls.txt", "w") as f:
            for url in urls:
                f.write(url + "\n")
        subprocess.run(
            ["arjun", "-i", "arjun_urls.txt", "-oT", arjun_out, "-t", "10", "-d", "0.5"],
            stderr=subprocess.DEVNULL, check=True, timeout=300
        )
        random_delay(intensity)
        if os.path.isfile(arjun_out):
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
        logger.error(f"Parameter discovery failed: {e}")
    context['vuln_urls'] = vulnerable_urls
    print_found("Parameter discovery", len(vulnerable_urls))
    timer_end(start, "Parameter discovery")

def step_advanced_xss(domain, config, context):
    print_step("Scanning for XSS vulnerabilities")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    error_log = os.path.join(outdir, domain, "errors.log")
    dalfox_out = os.path.join(outdir, domain, "dalfox.txt")
    xsstrike_out = os.path.join(outdir, domain, "xsstrike.txt")
    paramspider_out = os.path.join(outdir, domain, "paramspider.txt")
    try:
        subprocess.run([
            "dalfox", "file", paramspider_out,
            "--custom-payload", "/usr/share/xss-payloads.txt",
            "--output", dalfox_out,
            "--user-agent", get_random_user_agent(),
            "--delay", "500",
            "--timeout", "5"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        random_delay(intensity)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"dalfox failed: {e}\n")
        logger.error(f"dalfox failed: {e}")
    try:
        proxy = get_proxy()
        cmd = [
            "xsstrike", "-u", f"https://{domain}",
            "--file-log", xsstrike_out,
            "--headers", f"User-Agent: {get_random_user_agent()}",
            "--delay", "0.5",
            "--timeout", "5"
        ]
        if proxy:
            cmd.extend(["--proxy", proxy.get("http")])
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        random_delay(intensity)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"xsstrike failed: {e}\n")
        logger.error(f"xsstrike failed: {e}")
    context['xss'] = [dalfox_out, xsstrike_out]
    print_found("XSS scan files", 2)
    timer_end(start, "XSS scanning")

def step_dir_fuzz(domain, config, context):
    print_step("Directory and file fuzzing")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    error_log = os.path.join(outdir, domain, "errors.log")
    result_file = os.path.join(outdir, domain, "dir_fuzz.txt")
    fuzz_results = []
    scan_config = context.get("scan_config", {})
    if intensity == "light":
        wordlist = "/usr/share/seclists/Discovery/Web-Content/raft-small-words.txt"
        threads = 5
    elif intensity == "medium":
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"
        threads = 10
    else:
        wordlist = "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt"
        threads = 30
    tool = scan_config.get("dir_fuzz_tool", "ffuf")
    if tool == "dirsearch":
        try:
            subprocess.run([
                "dirsearch", "-u", f"https://{domain}",
                "-w", wordlist,
                "-t", str(threads),
                "-o", result_file,
                "--format", "plain",
                "--random-agent",
                "--timeout", "5",
                "--delay", "0.5"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=600)
            if os.path.isfile(result_file):
                with open(result_file) as f:
                    for line in f:
                        m = re.match(r"\[.*\] (http[^\s]+)", line)
                        if m:
                            fuzz_results.append(m.group(1))
            random_delay(intensity)
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"dirsearch failed: {e}\n")
            logger.error(f"dirsearch failed: {e}")
    else:
        try:
            subprocess.run([
                "ffuf", "-u", f"https://{domain}/FUZZ",
                "-w", wordlist,
                "-t", str(threads),
                "-of", "csv",
                "-o", result_file,
                "-H", f"User-Agent: {get_random_user_agent()}",
                "-timeout", "5",
                "-rate", "50",
                "-mc", "200,301,302"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=600)
            if os.path.isfile(result_file):
                with open(result_file) as f:
                    for line in f:
                        if line.startswith("url"):
                            continue
                        parts = line.strip().split(",")
                        if len(parts) > 0 and parts[0].startswith("http"):
                            fuzz_results.append(parts[0])
            random_delay(intensity)
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"ffuf failed: {e}\n")
            logger.error(f"ffuf failed: {e}")
    fuzz_results = sorted(set(fuzz_results))
    with open(result_file, "a") as f:
        f.write("\n# Deduped Fuzz Results\n")
        for path in fuzz_results:
            f.write(path + "\n")
    context['dir_fuzz'] = fuzz_results
    print_found("Directory fuzz", len(fuzz_results))
    timer_end(start, "Directory fuzzing")

def step_sqlmap(domain, config, context):
    print_step("Running SQL injection tests")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    vuln_urls = context.get('vuln_urls', [])
    error_log = os.path.join(outdir, domain, "errors.log")
    sqlmap_logs = []
    for i, url in enumerate(vuln_urls):
        sqlmap_dir = os.path.join(outdir, domain, f"sqlmap_{i+1}")
        os.makedirs(sqlmap_dir, exist_ok=True)
        try:
            subprocess.run([
                "sqlmap", "-u", url, "--batch",
                "--output-dir", sqlmap_dir,
                "--random-agent",
                "--delay", "0.5",
                "--timeout", "5",
                "--tamper", "space2comment,randomcase"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
            sqlmap_logs.append(sqlmap_dir)
            random_delay(intensity)
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"sqlmap on {url} failed: {e}\n")
            logger.error(f"sqlmap on {url} failed: {e}")
    context['sqlmap'] = sqlmap_logs
    print_found("SQLMap scans", len(sqlmap_logs))
    timer_end(start, "SQL injection testing")

def step_nuclei_chain(domain, config, context):
    print_step("Running nuclei chain scan")
    start = timer_start()
    outdir = config.get("output_dir") or "output"
    intensity = config.get("intensity", "medium")
    error_log = os.path.join(outdir, domain, "errors.log")
    nuclei_targets = set()
    nuclei_targets.update(context.get('live_subdomains', []))
    nuclei_targets.update(context.get('dir_fuzz', []))
    nuclei_targets.update(context.get('juicy', []))
    nuclei_targets.update(context.get('sensitive_files', []))
    nuclei_targets.update(context.get('vuln_urls', []))
    if os.path.isfile(context.get('waybackurls', '')):
        with open(context['waybackurls']) as f:
            nuclei_targets.update(line.strip() for line in f if line.strip())
    agg_urls = []
    for u in nuclei_targets:
        if isinstance(u, str):
            if u.startswith("http://") or u.startswith("https://"):
                agg_urls.append(u)
            else:
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
    nuclei_targets_file = os.path.join(outdir, domain, "nuclei_targets.txt")
    with open(nuclei_targets_file, "w") as f:
        for url in agg_urls:
            f.write(url + "\n")
    nuclei_out = os.path.join(outdir, domain, "nuclei_chained.txt")
    try:
        subprocess.run([
            "nuclei",
            "-l", nuclei_targets_file,
            "-o", nuclei_out,
            "-silent",
            "-c", str(context.get("scan_config", {}).get("threads", 10)),
            "-H", f"User-Agent: {get_random_user_agent()}",
            "-t", "5",
            "-rl", "50"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=600)
        random_delay(intensity)
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"Nuclei chained scan failed: {e}\n")
        logger.error(f"Nuclei chained scan failed: {e}")
    context['nuclei_chained'] = nuclei_out
    count = 0
    if os.path.isfile(nuclei_out):
        with open(nuclei_out) as f:
            count = sum(1 for _ in f)
    print_found("Nuclei findings", count)
    timer_end(start, "Nuclei chain scan")

def step_report(domain, config, context):
    print_step("Generating HTML report")
    start = timer_start()
    generate_report(domain, config, context)
    timer_end(start, "Report generation")

# ---- Intensity-Driven Pipeline ----

_INTENSITY_STEPS = [
    (step_check_dependencies, "light"),
    (step_subdomain_enum, "light"),
    (step_wayback_urls, "light"),
    (step_sensitive_file_enum, "light"),
    (step_report, "light"),
    (step_juicy_info, "medium"),
    (step_param_discovery, "medium"),
    (step_dir_fuzz, "medium"),
    (step_sqlmap, "medium"),
    (step_nuclei_chain, "medium"),
    (step_advanced_xss, "heavy"),
]

_INTENSITY_ORDER = {"light": 0, "medium": 1, "heavy": 2}

def get_steps_for_intensity(intensity):
    allowed = _INTENSITY_ORDER.get(intensity, 1)
    steps = []
    for step, level in _INTENSITY_STEPS:
        if _INTENSITY_ORDER[level] <= allowed:
            steps.append(step)
    return steps

def run_scan(domain, config, context):
    intensity = config.get("intensity", "medium")
    steps = get_steps_for_intensity(intensity)
    for step in steps:
        step(domain, config, context)

# For backward compatibility, export get_steps_for_intensity
scanner_steps = get_steps_for_intensity
