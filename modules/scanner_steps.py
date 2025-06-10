import os
import re
import subprocess
import time
import hashlib
import logging
import random
import requests
import urllib3
import json
from modules.reporter import generate_report
from modules.dependencies import check_dependencies
from urllib.parse import urlparse

try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None

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

def print_found(step, count, unique_count=None):
    msg = f"{step} - Found {count} (Unique: {unique_count if unique_count is not None else count})"
    print_step(msg)

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
    proxies = []
    return random.choice(proxies) if proxies else None

def random_delay(intensity):
    if intensity == "light":
        time.sleep(random.uniform(0.2, 0.6))
    elif intensity == "medium":
        time.sleep(random.uniform(0.6, 1.5))
    else:
        time.sleep(random.uniform(1, 3))

def run_command(cmd, timeout, error_log, capture_output=False):
    try:
        result = subprocess.run(
            cmd,
            check=True,
            timeout=timeout,
            stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout if capture_output else None
    except subprocess.SubprocessError as e:
        error_msg = f"Command {cmd} failed: {e}\nStderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}"
        try:
            with open(error_log, "a", encoding='utf-8') as ferr:
                ferr.write(error_msg + "\n")
        except Exception as log_err:
            logger.error(f"Failed to write to error log {error_log}: {log_err}")
        logger.error(error_msg)
        return None

def step_check_dependencies(domain, config, context):
    print_step("Checking dependencies")
    outdir = config.get("output_dir", "output")
    os.makedirs(outdir, exist_ok=True)
    error_log = os.path.join(outdir, f"{domain}/errors.log")
    try:
        check_dependencies(outdir)
        context['dependencies'] = True
        print_found("Dependencies", len(check_dependencies.__dict__.get('REQUIRED_TOOLS', [])))
    except Exception as e:
        try:
            with open(error_log, "a", encoding='utf-8') as ferr:
                ferr.write(f"Dependency check failed: {e}\n")
        except Exception as log_err:
            logger.error(f"Failed to write to error log {error_log}: {log_err}")
        logger.error(f"Dependency check failed: {e}")
        raise SystemExit(f"Dependency check failed: {e}")

def step_subdomain_enum(domain, config, context):
    print_step("Enumerating subdomains")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    subfinder_out = os.path.join(domain_dir, "subfinder.txt")
    all_subs_out = os.path.join(domain_dir, "all_subdomains.txt")
    live_out = os.path.join(domain_dir, "live_subdomains.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    subs = set()

    random_delay(intensity)
    stdout = run_command(
        ["subfinder", "-silent", "-d", domain, "-o", subfinder_out, "-t", "10", "-timeout", "5"],
        timeout=180,
        error_log=error_log,
        capture_output=True
    )
    if stdout:
        with open(subfinder_out, "w", encoding='utf-8') as f:
            f.write(stdout)
        with open(subfinder_out, "r", encoding='utf-8') as f:
            subs.update(line.strip() for line in f if line.strip())

    sources = ["bing", "dnsdumpster"]
    for source in sources:
        random_delay(intensity)
        proxy = get_proxy()
        harvester_out = os.path.join(domain_dir, f"theharvester_{source}.txt")
        cmd = ["theHarvester", "-d", domain, "-b", source]
        if proxy:
            cmd.extend(["--proxy", proxy.get("http")])
        stdout = run_command(cmd, timeout=300, error_log=error_log, capture_output=True)
        if stdout:
            with open(harvester_out, "w", encoding='utf-8') as f:
                f.write(stdout)
            try:
                for token in re.findall(rf"[\w\-\.]+{re.escape(domain)}", stdout):
                    subs.add(token.strip('",[]()<>'))
            except Exception as e:
                try:
                    with open(error_log, "a", encoding='utf-8') as ferr:
                        ferr.write(f"Parse theHarvester {source} failed: {e}\n")
                except Exception as log_err:
                    logger.error(f"Failed to write to error log {error_log}: {log_err}")
                logger.error(f"Parse theHarvester {source} failed: {e}")

    with open(all_subs_out, "w", encoding='utf-8') as f:
        for s in sorted(subs):
            f.write(f"{s}\n")
    context['subdomains'] = list(subs)

    print_step("Probing live subdomains")
    live_subs = set()
    try:
        probe = subprocess.Popen(
            ["httprobe", "-c", "50", "-t", "5000", "-p", "http:80,https:443"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        with open(all_subs_out, "r", encoding='utf-8') as f:
            out, err = probe.communicate(input=f.read(), timeout=120)
            if err:
                try:
                    with open(error_log, "a", encoding='utf-8') as ferr:
                        ferr.write(f"httprobe stderr: {err}\n")
                except Exception as log_err:
                    logger.error(f"Failed to write to error log {error_log}: {log_err}")
            for line in out.splitlines():
                host = line.strip().replace('http://', '').replace('https://', '').split('/')[0]
                if host:
                    live_subs.add(host)
    except Exception as e:
        try:
            with open(error_log, "a", encoding='utf-8') as ferr:
                ferr.write(f"httprobe failed: {e}\n")
        except Exception as log_err:
            logger.error(f"Failed to write to error log {error_log}: {log_err}")
        logger.error(f"httprobe failed: {e}")

    with open(live_out, "w", encoding='utf-8') as f:
        for s in sorted(live_subs):
            f.write(f"{s}\n")
    context['live_subdomains'] = list(live_subs)
    print_found("Subdomains", len(subs), len(subs))
    print_found("Live subdomains", len(live_subs), len(live_subs))
    timer_end(start, "Subdomain enumeration")

def step_wayback_urls(domain, config, context):
    print_step("Fetching wayback URLs")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    wayback_file = os.path.join(domain_dir, "waybackurls.txt")
    gau_file = os.path.join(domain_dir, "gau.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    random_delay(intensity)
    stdout = run_command(
        ["waybackurls", domain],
        timeout=600,
        error_log=error_log,
        capture_output=True
    )
    if stdout:
        with open(wayback_file, "w", encoding='utf-8') as f:
            f.write(stdout)

    if not os.path.isfile(wayback_file) or os.path.getsize(wayback_file) == 0:
        print_step("Falling back to gau for URL fetching")
        random_delay(intensity)
        stdout = run_command(
            ["gau", domain, "--threads", "5"],
            timeout=300,
            error_log=error_log,
            capture_output=True
        )
        if stdout:
            with open(gau_file, "w", encoding='utf-8') as f:
                f.write(stdout)
            context['waybackurls'] = gau_file
        else:
            context['waybackurls'] = wayback_file
    else:
        context['waybackurls'] = wayback_file

    urls = set()
    url_file = context['waybackurls']
    if os.path.isfile(url_file):
        with open(url_file, "r", encoding='utf-8') as f:
            urls.update(line.strip() for line in f if line.strip())
    print_found("Wayback URLs", len(urls), len(urls))
    timer_end(start, "Wayback URLs fetching")

def step_sensitive_file_enum(domain, config, context):
    print_step("Extracting sensitive files")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    wayback_file = context.get('waybackurls', os.path.join(domain_dir, "waybackurls.txt"))
    sensitive_file = os.path.join(domain_dir, "sensitive_files.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    live_sensitive = set()

    urllib3.disable_warnings()

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

    if os.path.isfile(wayback_file) and os.path.getsize(wayback_file) > 0:
        try:
            with open(wayback_file, "r", encoding='utf-8') as fin:
                urls = [line.strip() for line in fin if re.search(sensitive_regex, line, re.I)]
            with open(sensitive_file, "w", encoding='utf-8') as fout:
                found = False
                for url in urls:
                    is_live, has_sensitive = step_live_check(url, sensitive_keywords)
                    if is_live:
                        found = True
                        mark = "[SENSITIVE]" if has_sensitive else "[LIVE]"
                        fout.write(f"{mark} {url}\n")
                        if has_sensitive:
                            live_sensitive.add(url)
                    random_delay(intensity)
                if found:
                    fout.write(f"\n# Sensitive Files and Links for {domain}\n")
                else:
                    fout.write("No sensitive files or links found.\n")
        except Exception as e:
            try:
                with open(error_log, "a", encoding='utf-8') as ferr:
                    ferr.write(f"Failed to extract sensitive files: {e}\n")
            except Exception as log_err:
                logger.error(f"Failed to write to error log {error_log}: {log_err}")
            logger.error(f"Failed to extract sensitive files: {e}")
    else:
        with open(sensitive_file, "w", encoding='utf-8') as fout:
            fout.write("No URLs available for sensitive file enumeration.\n")
        logger.warning("No URLs available for sensitive file enumeration.")

    context['sensitive_files'] = list(live_sensitive)
    print_found("Sensitive files/URLs", len(live_sensitive), len(live_sensitive))
    timer_end(start, "Sensitive file enumeration")

def step_live_check(url, keywords=None):
    try:
        headers = {"User-Agent": get_random_user_agent()}
        proxy = get_proxy()
        r = requests.get(
            url, headers=headers, proxies=proxy, timeout=8, allow_redirects=False,
            verify=False
        )
        body = r.text.lower()
        has_sensitive = any(kw in body for kw in (keywords or []))
        is_live = r.status_code in [200, 301, 302]
        return is_live, has_sensitive
    except Exception as e:
        logger.debug(f"Live check failed for {url}: {e}")
        return False, False

def step_juicy_info(domain, config, context):
    print_step("Scanning for juicy info (secrets, keys, tokens, JS)")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    wayback_file = context.get('waybackurls', os.path.join(domain_dir, "waybackurls.txt"))
    juicy_file = os.path.join(domain_dir, "juicy_info")
    js_dir = os.path.join(domain_dir, "js_files")
    os.makedirs(js_dir, exist_ok=True)
    error_log = os.path.join(domain_dir, "errors.log")
    live_juicy = set()

    patterns = [
        r"api[_-]?key", r"token", r"password", r"secret", r"timeout", r"access[_-]?key", r"aws[_-]?key",
        r"aws[_-]?secret", r"auth[_-]?token", r"session[_-]?id", r"credential", r"stripe[_-]?key",
        r"s3\.amazonaws\.com", r"blob\.timeout", r"firebase",
        r"client[_-]?id", r"client[_]?secret",
        r"oauth[_-]?access_token", r"db[_]?password", r"database[_]?url", r"[0-9a-f]{32,}",
        r"key=[a-zA-Z0-9_-]+", r"jwt=[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
        r"mongodb://", r"mysql://", r"postgres://", r"slack[_-]?token",
        r"bearer[_-]?token"
    ]
    false_positives = [
        "csrf_token", "xsrf_token", "sessionid", "nonce", "token_validation", "form_token"
    ]
    pattern_regex = f"({r'|'.join(patterns)})"

    found = False
    if os.path.isfile(wayback_file) and os.path.getsize(wayback_file) > 0:
        try:
            with open(wayback_file, "r", encoding='utf-8') as fin:
                urls = set(line.strip() for line in fin if re.search(pattern_regex, line, re.I))
            with open(juicy_file, "w", encoding='utf-8') as fout:
                for url in urls:
                    if any(fp in url for fp in false_positives):
                        continue
                    is_live, has_sensitive = step_live_check(url, None)
                    if is_live:
                        found = True
                        fout.write(f"[LIVE] {url}\n")
                        live_juicy.add(url)
                    random_delay(intensity)

                with open(wayback_file, "r", encoding='utf-8') as fin:
                    js_urls = set(line.strip() for line in fin if re.search(r'\.js$', line.lower()))
                for url in sorted(js_urls):
                    filename = hashlib.sha1(url.encode()).hexdigest() + ".js"
                    js_path = os.path.join(js_dir, filename)
                    try:
                        headers = {"User-Agent": get_random_user_agent()}
                        proxy = get_proxy()
                        r = requests.get(url, headers=headers, proxies=proxy, timeout=10, verify=False)
                        with open(js_path, "w", encoding='utf-8') as jsf:
                            jsf.write(r.text)
                        with open(js_path, "r", encoding='utf-8') as jsf:
                            for jsline in jsf:
                                if re.search(pattern_regex, jsline, re.I) and not any(re.search(fp, jsline, re.I) for fp in false_positives):
                                    fout.write(f"[JS] {url}: {jsline.strip()}\n")
                                    found = True
                                    live_juicy.add(url)
                        random_delay(intensity)
                    except Exception as e:
                        try:
                            with open(error_log, "a", encoding='utf-8') as ferr:
                                ferr.write(f"Failed to fetch JS {url}: {e}\n")
                        except Exception as log_err:
                            logger.error(f"Failed to write to error log {error_log}: {log_err}")
                        logger.error(f"Failed to fetch JS {url}: {e}")

                if found:
                    fout.write(f"\n# Juicy Info for {domain}\n")
                else:
                    fout.write("No juicy info found.\n")
        except Exception as e:
            try:
                with open(error_log, "a", encoding='utf-8') as ferr:
                    ferr.write(f"Failed to extract juicy info: {e}\n")
            except Exception as log_err:
                logger.error(f"Failed to write to error log {error_log}: {log_err}")
            logger.error(f"Failed to extract juicy info: {e}")
    else:
        with open(juicy_file, "w", encoding='utf-8') as fout:
            fout.write("No URLs available for juicy info extraction.\n")
        logger.warning("No URLs available for juicy info extraction.")

    context['juicy'] = list(live_juicy)
    print_found("Juicy info (URLs)", len(live_juicy), len(live_juicy))
    timer_end(start_time, "Juicy info extraction")

def step_param_discovery(domain, config, context):
    print_step("Discovering dynamic parameters")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    paramspider_out = os.path.join(domain_dir, "paramspider.txt")
    arjun_out = os.path.join(domain_dir, "arjun.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    vulnerable_urls = set()

    random_delay(intensity)
    stdout = run_command(
        ["paramspider", "-d", domain, "--output", paramspider_out, "--silent"],
        timeout=300,
        error_log=error_log,
        capture_output=True
    )
    if stdout and os.path.isfile(paramspider_out):
        urls = set()
        try:
            with open(paramspider_out, "r", encoding='utf-8') as f:
                for line in f:
                    if "http" in line.lower() and "=" in line:
                        urls.add(line.strip())
            if urls:
                with open(paramspider_out, "w", encoding='utf-8') as fout:
                    fout.write(f"# Parameter URLs for {domain}\n")
                    for url in sorted(urls):
                        fout.write(f"{url}\n")
                with open("arjun_urls.txt", "w", encoding='utf-8') as f:
                    for url in urls:
                        f.write(url + "\n")
                random_delay(intensity)
                stdout = run_command(
                    ["arjun", "-i", "arjun_urls.txt", "-oT", arjun_out, "-t", "10", "-d", "0.5"],
                    timeout=300,
                    error_log=error_log,
                    capture_output=True
                )
                if os.path.isfile(arjun_out):
                    with open(arjun_out, "r", encoding='utf-8') as f:
                        for line in f:
                            if "GET" in line or "POST" in line:
                                match = re.search(r"(http\S+)", line)
                                if match:
                                    vulnerable_urls.add(match.group(1))
                try:
                    os.remove("arjun_urls.txt")
                except:
                    pass
            else:
                with open(paramspider_out, "w", encoding='utf-8') as fout:
                    fout.write("No parameters found by ParamSpider.\n")
        except Exception as e:
            try:
                with open(error_log, "a", encoding='utf-8') as ferr:
                    ferr.write(f"Failed to process paramspider output: {e}\n")
            except Exception as log_err:
                logger.error(f"Failed to write to error log {error_log}: {log_err}")
            logger.error(f"Failed to process paramspider output: {e}")
    else:
        with open(paramspider_out, "w", encoding='utf-8') as fout:
            fout.write("No parameters found by ParamSpider.\n")
        logger.warning("No parameters found by ParamSpider.")

    context['vuln_urls'] = list(sorted(vulnerable_urls))
    print_found("Parameter discovery URLs", len(vulnerable_urls), len(vulnerable_urls))
    timer_end(start_time, "Parameter discovery")

def step_advanced_xss(domain, config, context):
    print_step("Scanning for XSS vulnerabilities")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    dalfox_file = os.path.join(domain_dir, "dalfox.txt")
    xsstrike_file = os.path.join(domain_dir, "xsstrike.txt")
    paramspider_file = os.path.join(domain_dir, "paramspider.txt")
    xss_results = []

    if os.path.isfile(paramspider_file) and os.path.getsize(paramspider_file) > 0:
        random_delay(intensity)
        stdout = run_command(
            [
                "dalfox", "file", paramspider_file,
                "--output", dalfox_file,
                "--user-agent", get_random_user_agent(),
                "--delay", "500",
                "--timeout", "5"
            ],
            timeout=500,
            error_log=error_log,
            capture_output=True
        )
        if stdout:
            with open(dalfox_file, "w", encoding='utf-8') as f:
                f.write(stdout)
            xss_results.append(dalfox_file)
        else:
            with open(dalfox_file, "w", encoding='utf-8') as f:
                f.write("No XSS vulnerabilities found by Dalfox.\n")
    else:
        with open(dalfox_file, "w", encoding='utf-8') as f:
            f.write("No URLs available for Dalfox XSS scan.\n")
        logger.warning("No parameters available for Dalfox XSS scan.")

    random_delay(intensity)
    proxy = get_proxy()
    cmd = [
        "xsstrike", "-u", f"https://{domain}",
        "--file-log", xsstrike_file,
        "--headers", f"User-Agent: {get_random_user_agent()}",
        "--delay", "0.5",
        "--timeout", "5"
    ]
    if proxy:
        cmd.extend(["--proxy", proxy.get("http", "")])
    stdout = run_command(cmd, timeout=300, error_log=error_log, capture_output=True)
    if stdout:
        with open(xsstrike_file, "w", encoding='utf-8') as f:
            f.write(stdout)
        xss_results.append(xsstrike_file)
    else:
        with open(xsstrike_file, "w", encoding='utf-8') as f:
            f.write("No XSS vulnerabilities found by XSStrike.\n")

    context['xss'] = xss_results
    print_found("XSS scan results", len(xss_results), len(set(xss_results)))
    timer_end(start_time, "XSS scanning")

def step_dir_fuzz(domain, config, context):
    print_step("Directory and file fuzzing")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    result_file = os.path.join(domain_dir, "dir_fuzz.txt")
    fuzz_results = []

    if intensity == "light":
        wordlist = "/usr/share/seclists/Discovery/Web-Content/raft-small-words.txt"
        threads = 8
        timeout = 300
    elif intensity == "medium":
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"
        threads = 10
        timeout = 600
    else:
        wordlist = "/usr/share/seclists/Discovery/Web-Content/raft-large-files.txt"
        threads = 20
        timeout = 900

    tool = config.get("dir_fuzz_tool", "ffuf")

    if tool == "dirsearch":
        random_delay(intensity)
        stdout = run_command(
            [
                "dirsearch", "-u", f"https://{domain}",
                "-w", wordlist,
                "-t", str(threads),
                "-o", result_file,
                "--format", "plain",
                "--random-agent",
                "--timeout", "5",
                "--delay", "0.5"
            ],
            timeout=timeout,
            error_log=error_log,
            capture_output=True
        )
        if stdout and os.path.isfile(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                try:
                    for line in f:
                        m = re.search(r"\[.*\]\s*(http\S+)", line)
                        if m:
                            fuzz_results.append(m.group(1))
                except Exception as e:
                    try:
                        with open(error_log, "a", encoding='utf-8') as ferr:
                            ferr.write(f"Failed to parse dirsearch output: {e}\n")
                    except Exception as log_err:
                        logger.error(f"Failed to write to error log {error_log}: {log_err}")
                    logger.error(f"Failed to parse dirsearch output: {e}")
    else:
        random_delay(intensity)
        stdout = run_command(
            [
                "ffuf", "-u", f"https://{domain}/FUZZ",
                "-w", wordlist,
                "-t", str(threads),
                "-of", "json",
                "-o", result_file,
                "-H", f"User-Agent: {get_random_user_agent()}",
                "-timeout", "5",
                "-rate", "50",
                "-mc", "200,301,302"
            ],
            timeout=timeout,
            error_log=error_log,
            capture_output=True
        )
        if os.path.isfile(result_file):
            try:
                with open(result_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    for result in data.get("results", []):
                        url = result.get("url")
                        status = result.get("status")
                        size = result.get("length")
                        if url and status in [200, 301, 302]:
                            fuzz_results.append({"url": url, "status": status, "size": size})
            except Exception as e:
                try:
                    with open(error_log, "a", encoding='utf-8') as ferr:
                        ferr.write(f"Failed to parse FFuf output: {e}\n")
                except Exception as log_err:
                    logger.error(f"Failed to write to error log {error_log}: {log_err}")
                logger.error(f"Failed to parse FFuf output: {e}")

        unique_results = {r["url"] for r in fuzz_results}
        with open(result_file, "w", encoding='utf-8') as f:
            f.write(f"# Directory Fuzzing Results for {domain}\n")
            f.write("URL | Status | Size\n")
            f.write("-" * 80 + "\n")
            for r in sorted(fuzz_results, key=lambda x: x["url"]):
                f.write(f"{r['url']} | {r['status']} | {r['size']}\n")
            f.write(f"\n# Summary\n# Total Found: {len(fuzz_results)}\n# Unique URLs: {len(unique_results)}\n")

    context['dir_fuzz'] = [r["url"] for r in fuzz_results]
    print_found("Directory fuzz URLs", len(fuzz_results), len(unique_results))
    timer_end(start_time, "Directory fuzzing")

def step_sqlmap(domain, config, context):
    print_step("Running SQL injection tests")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    timeout = 300 if intensity == "light" else 500 if intensity == "medium" else 800
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    vuln_urls = context.get('vuln_urls', [])
    sqlmap_logs = []

    for i, url in enumerate(vuln_urls[:10]):  # Limit to 10 URLs
        sqlmap_dir = os.path.join(domain_dir, f"sqlmap_{i+1}")
        os.makedirs(sqlmap_dir, exist_ok=True)

        random_delay(intensity)
        stdout = run_command(
            [
                "sqlmap", "-u", url, "--batch",
                "--output-dir", sqlmap_dir,
                "--random-agent",
                "--delay", "0.5",
                "--timeout", "5",
                "--tamper", "space2comment"
            ],
            timeout=timeout,
            error_log=error_log,
            capture_output=True
        )
        if os.path.isdir(sqlmap_dir) and os.listdir(sqlmap_dir):
            sqlmap_logs.append(sqlmap_dir)
        random_delay(intensity)

    context['sqlmap'] = sqlmap_logs
    print_found("SQLMap scan directories", len(sqlmap_logs), len(set(sqlmap_logs)))
    timer_end(start_time, "SQL injection testing")

def step_nuclei_chain(domain, config, context):
    print_step("Scanning for vulnerabilities with Nuclei")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    timeout = 300 if intensity == "light" else 600
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    nuclei_targets = set()

    nuclei_targets.update(context.get('live_subdomains', []))
    nuclei_targets.update(context.get('dir_fuzz', []))
    nuclei_targets.update(context.get('juicy', []))
    nuclei_targets.update(context.get('sensitive_files', []))
    nuclei_targets.update(context.get('vuln_urls', []))
    if os.path.isfile(context.get('waybackurls', '')):
        with open(context['waybackurls'], "r", encoding='utf-8') as f:
            nuclei_targets.update(line.strip().rstrip() for line in f if line.strip())

    agg_urls = []
    for u in nuclei_targets:
        if isinstance(u, str):
            if u.startswith("http"):
                agg_urls.append(u)
            else:
                agg_urls.append(f"http://{u}")
                agg_urls.append(f"https://{u}")
        elif isinstance(u, list):
            for v in u:
                if v.startswith("http"):
                    agg_urls.append(v)
                else:
                    agg_urls.append(f"http://{v}")
                    agg_urls.append(f"https://{v}")

    agg_urls = sorted(set(agg_urls))
    nuclei_targets_file = os.path.join(domain_dir, "nuclei_targets.txt")
    with open(nuclei_targets_file, "w", encoding='utf-8') as f:
        for u in agg_urls:
            f.write(f"{u}\n")

    nuclei_out = os.path.join(domain_dir, "nuclei.txt")

    if os.path.isfile(nuclei_targets_file) and os.path.getsize(nuclei_targets_file) > 0:
        random_delay(intensity)
        stdout = run_command(
            [
                "nuclei", "-l", nuclei_targets_file,
                "-o", nuclei_out,
                "-silent",
                "-c", str(config.get("threads", 10)),
                "-H", f"User-Agent: {get_random_user_agent()}",
                "-t", "5",
                "-rl", "30"
            ],
            timeout=timeout,
            error_log=error_log,
            capture_output=True
        )
    else:
        with open(nuclei_out, "w", encoding='utf-8') as f:
            f.write("No targets available for Nuclei scan.\n")
        logger.warning("No targets available for Nuclei scan.")

    findings = set()
    if os.path.isfile(nuclei_out):
        with open(nuclei_out, "r", encoding='utf-8') as f:
            for line in f:
                try:
                    if line.strip() and not line.startswith("#"):
                        findings.add(line.strip())
                except Exception as e:
                    logger.debug(f"Failed to parse nuclei line: {line}: {e}")

    context['nuclei_chained'] = nuclei_out
    print_found("Nuclei vulnerabilities", len(findings), len(findings))
    timer_end(start_time, "Nuclei scan")

def step_report(domain, config, context):
    print_step("Generating scan report")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    try:
        generate_report(domain, config, context)
        print_found("Report files", 1, 1)
    except Exception as e:
        try:
            with open(error_log, "a", encoding='utf-8') as ferr:
                ferr.write(f"Failed to generate report: {e}\n")
        except Exception as log_err:
            logger.error(f"Failed to write to error log {error_log}: {log_err}")
        logger.error(f"Failed to generate report: {e}")
    timer_end(start_time, "Report generation")

_INTENSIITY_STEPS = [
    (step_check_dependencies, "light"),
    (step_subdomain_enum, "light"),
    (step_wayback_urls, "light"),
    (step_sensitive_file_enum, "light"),
    (step_juicy_info, "medium"),
    (step_param_discovery, "medium"),
    (step_dir_fuzz, "medium"),
    (step_sqlmap, "medium"),
    (step_nuclei_chain, "medium"),
    (step_advanced_xss, "heavy"),
    (step_report, "light")
]

_INTENSIITY_ORDER = {"light": 0, "medium": 1, "heavy": 2}

def get_steps_for_intensity(intensity):
    allowed = _INTENSIITY_ORDER.get(intensity, 2)
    steps = []
    for step, level in _INTENSIITY_STEPS:
        if _INTENSIITY_ORDER.get(level, 2) <= allowed:
            steps.append(step)
    return steps

def run_scan(domain, config, context):
    intensity = config.get("intensity", "medium")
    steps = get_steps_for_intensity(intensity)
    for step in steps:
        try:
            step(domain, config, context)
        except Exception as e:
            logger.error(f"Step {step.__name__} failed: {e}")
            continue
    print_step("\nScan completed successfully!")
