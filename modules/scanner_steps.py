import os
import re
import shutil
import subprocess
import time
import logging
import random
import requests
import urllib3
import json
import traceback
import hashlib
from urllib.parse import urlparse
from modules.reporter import generate_report
from modules.dependencies import check_dependencies

try:
    from rich.console import Console
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def color(text, clr, bold=False):
    if not RICH_AVAILABLE:
        codes = {
            "green": "1;32", "red": "1;31", "yellow": "1;33", "cyan": "1;36",
            "magenta": "1;35", "bold": "1", "white": "1;37"
        }
        style = []
        if bold:
            style.append(codes["bold"])
        if clr in codes:
            style.append(codes[clr])
        return f"\033[{';'.join(style)}m{text}\033[0m"
    tag = f"bold {clr}" if bold else clr
    return f"[{tag}]{text}[/{tag}]"

def print_step(msg):
    msg = f"[VENO] {msg}"
    if console:
        console.print(f"[cyan]{msg}[/cyan]")
    else:
        print(color(msg, "cyan"))
    logger.info(msg)

def print_found(step, count, unique_count=None):
    msg = f"{step} - Found {count} (Unique: {unique_count if unique_count is not None else count})"
    print_step(msg)

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

def alert(title, data_list):
    if not data_list:
        return
    message = f"\n🚨 [ALERT] {title.upper()} FOUND:\n" + "\n".join(f"- {item}" for item in data_list[:10])
    if console:
        console.print(color(message, "red", bold=True))
    else:
        print(color(message, "red", bold=True))

def alert_error(msg, error_log):
    message = f"\n🚨 [ERROR] {msg}"
    if console:
        console.print(color(message, "red", bold=True))
    else:
        print(color(message, "red", bold=True))
    try:
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except Exception as log_err:
        logger.error(f"Failed to write to error log {error_log}: {log_err}")

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
    proxies = []  # Populate with proxies, e.g., [{"http": "http://proxy:port"}]
    if not proxies:
        logger.debug("No proxies configured")
        return None
    return random.choice(proxies)

def random_delay(intensity):
    delays = {
        "light": (0.5, 1.5),
        "medium": (0.6, 2.0),
        "heavy": (0.1, 1.0)
    }
    min_delay, max_delay = delays.get(intensity, delays["medium"])
    time.sleep(random.uniform(min_delay, max_delay))

def run_command(cmd, timeout, error_log, capture_output=False, stdout=None):
    os.makedirs(os.path.dirname(error_log), exist_ok=True)
    try:
        result = subprocess.run(
            cmd,
            check=True,
            timeout=timeout,
            stdout=stdout if stdout else subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout if capture_output else None
    except subprocess.SubprocessError as exc:
        error_msg = f"Command {' '.join(cmd)} failed: {str(exc)}\nStderr: {exc.stderr if hasattr(exc, 'stderr') else 'N/A'}\nStack trace: {traceback.format_exc()}"
        try:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(error_msg + "\n")
        except Exception as log_err:
            logger.error(f"Failed to write to error log {error_log}: {log_err}")
        logger.error(error_msg)
        return None

def step_check_dependencies(domain, config, context):
    print_step("Checking dependencies")
    error_log = os.path.join(config.get("output_dir", "."), domain, "errors.log")
    os.makedirs(os.path.dirname(error_log), exist_ok=True)
    try:
        check_dependencies(config)
        context["dependencies"] = True
        print_step("All dependencies satisfied")
    except Exception as exc:
        error_msg = f"Dependency check failed: {str(exc)}\nStack trace: {traceback.format_exc()}"
        try:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(error_msg + "\n")
        except Exception as log_err:
            logger.error(f"Failed to write to error log {error_log}: {log_err}")
        logger.error(error_msg)
        context["failures"] = context.get("failures", []) + [("Dependencies", str(exc))]
        raise
def step_subdomain_enum(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🔍 Enumerating subdomains")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    all_subs_out = os.path.join(domain_dir, "all_subdomains.txt")
    live_out = os.path.join(domain_dir, "live_subdomains.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    subs = set()
    live_subs = set()

    try:
        # Subfinder
        random_delay(intensity)
        stdout = run_command(
            ["subfinder", "-silent", "-d", domain, "-t", "10", "-timeout", "5"],
            timeout=180,
            error_log=error_log,
            capture_output=True
        )
        if stdout:
            subs.update(line.strip() for line in stdout.splitlines())

        # Fallback: theHarvester
        if not subs:
            for src in ["crtsh", "anubis", "certspotter"]:
                cmd = ["theHarvester", "-d", domain, "-b", src]
                output = run_command(cmd, timeout=300, error_log=error_log, capture_output=True)
                if output:
                    subs.update(re.findall(rf"[\w\-.]+\.{re.escape(domain)}", output))

        if not subs:
            alert("Subdomain Enum", ["No subdomains found"])
            context.setdefault("failures", []).append(("Subdomain Enum", "No subs"))
        else:
            with open(all_subs_out, "w", encoding="utf-8") as f:
                for sub in sorted(subs):
                    f.write(f"{sub}\n")
            context["subdomains"] = sorted(subs)

        # httprobe
        if subs:
            print_step("⚡ Probing with httprobe")
            try:
                probe = subprocess.Popen(
                    ["httprobe", "-c", "50", "-t", "5000", "-p", "http:80,https:443"],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                input_data = "\n".join(subs)
                out, err = probe.communicate(input=input_data, timeout=120)
                if err:
                    with open(error_log, "a", encoding="utf-8") as ef:
                        ef.write(f"[httprobe] stderr: {err}\n")
                for line in out.splitlines():
                    host = line.strip().split("//")[-1].split("/")[0]
                    live_subs.add(host)
            except Exception as exc:
                alert_error("httprobe failed", error_log)
                context.setdefault("failures", []).append(("httprobe", str(exc)))

            with open(live_out, "w", encoding="utf-8") as f:
                for host in sorted(live_subs):
                    f.write(f"{host}\n")
            context["live_subdomains"] = sorted(live_subs)

        print_found("Subdomains", len(subs), len(set(subs)))
        print_found("Live Subdomains", len(live_subs), len(set(live_subs)))

    except Exception as exc:
        alert_error(f"Subdomain enumeration failed: {exc}", error_log)
        context.setdefault("failures", []).append(("Subdomain Enum", str(exc)))
    timer_end(start, "Subdomain enumeration")
def step_subjack_takeover(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity", "medium") != "deep":
        print_step("⏭️ Skipping Subjack scan (requires deep intensity)")
        return

    print_step("🎯 Checking for takeover with Subjack")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    error_log = os.path.join(domain_dir, "errors.log")
    subs = context.get("subdomains", [])
    if not subs:
        alert("Subjack", ["Missing subdomains from previous step"])
        context.setdefault("failures", []).append(("Subjack", "No input subs"))
        return

    input_file = os.path.join(domain_dir, "subjack_input.txt")
    output_file = os.path.join(domain_dir, "subjack_takeover.txt")
    takeovers = set()

    try:
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("\n".join(subs))

        cmd = [
            "subjack", "-w", input_file, "-o", output_file,
            "-t", str(config.get("threads", 10)), "-timeout", "5", "-ssl"
        ]
        run_command(cmd, timeout=300, error_log=error_log)

        if os.path.isfile(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        takeovers.add(line.strip())
        context["subjack_takeovers"] = sorted(takeovers)

        print_found("Potential Takeovers", len(takeovers))
        if takeovers:
            alert("Subjack Takeovers", list(takeovers))
        else:
            alert("Subjack", ["No vulnerable takeovers found."])

    except Exception as e:
        alert_error(f"Subjack failed: {e}", error_log)
        context.setdefault("failures", []).append(("Subjack", str(e)))
    timer_end(start, "Subjack takeover scan")
def step_wayback_urls(domain, config, context):
    if context.get("skip", False):
        return
    print_step("📜 Fetching Wayback URLs")
    start = timer_start()
    intensity = config.get("intensity", "medium")
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    wayback_file = os.path.join(domain_dir, "waybackurls.txt")
    gau_file = os.path.join(domain_dir, "gau.txt")
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    urls = set()

    try:
        # Try waybackurls
        random_delay(intensity)
        stdout = run_command(["waybackurls", domain], timeout=300, error_log=error_log, capture_output=True)
        if stdout:
            with open(wayback_file, "w", encoding="utf-8") as f:
                f.write(stdout)
            urls.update(line.strip() for line in stdout.splitlines())

        # Fallback to gau
        if not urls and config.get("gau", True):
            print_step("🔁 Falling back to gau")
            stdout = run_command(["gau", domain, "--threads", "5"], timeout=300, error_log=error_log, capture_output=True)
            if stdout:
                with open(gau_file, "w", encoding="utf-8") as f:
                    f.write(stdout)
                urls.update(line.strip() for line in stdout.splitlines())
                context["wayback_urls"] = gau_file
            else:
                context["wayback_urls"] = wayback_file
        else:
            context["wayback_urls"] = wayback_file

        # Save to master URL list
        with open(all_urls_file, "a", encoding="utf-8") as f:
            for url in sorted(urls):
                f.write(f"{url}\n")

        context["urls"] = sorted(urls)
        print_found("Wayback URLs", len(urls))

        if not urls:
            alert("Wayback/Gau URLs", ["No archive URLs discovered"])
            context.setdefault("failures", []).append(("Wayback", "No URLs"))

    except Exception as e:
        alert_error(f"Wayback scraping failed: {e}", error_log)
        context.setdefault("failures", []).append(("Wayback", str(e)))

    timer_end(start, "Wayback URLs")

def step_waymore_urls(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping waymore (intensity: light)")
        return

    print_step("📦 Fetching URLs with Waymore")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    waymore_file = os.path.join(domain_dir, "waymore_urls.txt")
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    urls = set()

    try:
        random_delay(config.get("intensity"))
        run_command(
            ["waymore", "-i", domain, "-oU", waymore_file, "-mode", "U"],
            timeout=600,
            error_log=error_log
        )

        if os.path.isfile(waymore_file):
            with open(waymore_file, "r", encoding="utf-8") as f:
                urls.update(line.strip() for line in f if line.strip())

        with open(all_urls_file, "a", encoding="utf-8") as f:
            for url in sorted(urls):
                f.write(f"{url}\n")

        context["waymore_urls"] = sorted(urls)
        print_found("Waymore URLs", len(urls))

        if not urls:
            alert("Waymore URLs", ["No new URLs from Waymore"])
            context.setdefault("failures", []).append(("Waymore", "0 URLs"))

    except Exception as e:
        alert_error(f"Waymore failed: {e}", error_log)
        context.setdefault("failures", []).append(("Waymore", str(e)))

    timer_end(start, "Waymore URL Collection")

def step_parse_param_urls(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping param parsing (intensity: light)")
        return

    print_step("🔎 Extracting parameterized URLs")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    param_urls_file = os.path.join(domain_dir, "param_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    param_urls = set()

    param_regex = re.compile(r"\?.+=.+|\.(php|asp|aspx|jsp)(/|$)", re.I)

    try:
        if os.path.isfile(all_urls_file) and os.path.getsize(all_urls_file) > 0:
            with open(all_urls_file, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if param_regex.search(url):
                        param_urls.add(url)

            with open(param_urls_file, "w", encoding="utf-8") as f:
                for url in sorted(param_urls):
                    f.write(f"{url}\n")

            context["param_urls"] = sorted(param_urls)
            print_found("Param URLs", len(param_urls))

            if not param_urls:
                alert("Param Parsing", ["No parameter URLs found"])
                context.setdefault("failures", []).append(("Param Parse", "None"))
        else:
            with open(param_urls_file, "w", encoding="utf-8") as f:
                f.write("all_urls.txt missing or empty.\n")
            logger.warning("No all_urls.txt available")
            alert("Param Parse", ["all_urls.txt missing or empty"])
            context.setdefault("failures", []).append(("Param Parse", "Missing input"))

    except Exception as e:
        alert_error(f"Param parsing failed: {e}", error_log)
        context.setdefault("failures", []).append(("Param Parse", str(e)))

    timer_end(start, "Parameter URL Extraction")

def step_probe_param_urls(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping param probing (intensity: light)")
        return

    print_step("📡 Probing parameter URLs with httprobe")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    param_urls_file = os.path.join(domain_dir, "param_urls.txt")
    live_param_urls_file = os.path.join(domain_dir, "live_param_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    live_param_urls = set()

    urls = context.get("param_urls", [])
    if not urls and os.path.isfile(param_urls_file):
        with open(param_urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

    if not urls:
        with open(live_param_urls_file, "w", encoding="utf-8") as f:
            f.write("No parameter URLs available for probing.\n")
        logger.warning("No parameter URLs available.")
        alert("Live Param Probe", ["Missing input URLs"])
        context.setdefault("failures", []).append(("Probe Param URLs", "Missing input"))
        return

    try:
        probe = subprocess.Popen(
            ["httprobe", "-c", "50", "-t", "5000", "-p", "http:80,https:443"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        out, err = probe.communicate(input="\n".join(urls), timeout=120)

        if err:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"[httprobe] stderr: {err}\n")

        for line in out.splitlines():
            if line.strip():
                live_param_urls.add(line.strip())

        with open(live_param_urls_file, "w", encoding="utf-8") as f:
            for url in sorted(live_param_urls):
                f.write(f"{url}\n")

    except Exception as exc:
        alert_error("httprobe failed for param URLs", error_log)
        context.setdefault("failures", []).append(("Probe Param URLs", str(exc)))

    context["live_param_urls"] = sorted(live_param_urls)
    print_found("Live Param URLs", len(live_param_urls))

    if not live_param_urls:
        alert("Live Param URLs", ["None responded"])
        context.setdefault("failures", []).append(("Live Param URLs", "0 live detected"))

    timer_end(start, "Live Parameter URL Probing")

def step_param_discovery(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping param discovery (intensity: light)")
        return

    print_step("🕷️ Discovering dynamic parameters (ParamSpider + Arjun + Regex Grep)")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    paramspider_out = os.path.join(domain_dir, "paramspider.txt")
    arjun_input = os.path.join(domain_dir, "arjun_urls.txt")
    arjun_out = os.path.join(domain_dir, "arjun.txt")
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    urls = set()
    vuln_urls = set()

    # ===== ParamSpider Scan =====
    try:
        with open(paramspider_out, "w", encoding='utf-8') as fout:
            run_command(["paramspider", "-d", domain], timeout=300, error_log=error_log, stdout=fout)

        if os.path.isfile(paramspider_out):
            with open(paramspider_out, "r", encoding='utf-8') as f:
                for line in f:
                    if "http" in line and "=" in line:
                        urls.add(line.strip())

    except Exception as e:
        alert_error("ParamSpider failed", error_log)
        context.setdefault("failures", []).append(("ParamSpider", str(e)))

    # ===== Grep from all_urls.txt =====
    try:
        if os.path.isfile(all_urls_file) and os.path.getsize(all_urls_file) > 0:
            param_regex = re.compile(r"\?.+=.+|\.(php|asp|aspx|jsp)(\?|/|$)", re.I)
            with open(all_urls_file, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if param_regex.search(url):
                        urls.add(url)
    except Exception as e:
        alert_error("Failed to grep from all_urls.txt", error_log)
        context.setdefault("failures", []).append(("Param Grep", str(e)))

    # ===== Arjun Enumeration =====
    if urls:
        try:
            with open(arjun_input, "w", encoding="utf-8") as f:
                for url in sorted(urls):
                    f.write(f"{url}\n")

            random_delay(config.get("intensity"))
            run_command(
                ["arjun", "-i", arjun_input, "-oT", arjun_out, "-t", "10", "-d", "0.5"],
                timeout=300,
                error_log=error_log
            )

            if os.path.isfile(arjun_out):
                with open(arjun_out, "r", encoding="utf-8") as f:
                    for line in f:
                        match = re.search(r"(http\S+)", line)
                        if match:
                            vuln_urls.add(match.group(1))

            try:
                os.remove(arjun_input)
            except:
                pass

        except Exception as e:
            alert_error("Arjun failed", error_log)
            context.setdefault("failures", []).append(("Arjun", str(e)))

    context["vuln_urls"] = sorted(vuln_urls)
    print_found("Vuln Param URLs", len(vuln_urls))

    if not vuln_urls:
        alert("Param Discovery", ["No vulnerable parameters found"])
        context.setdefault("failures", []).append(("Param Discovery", "No vuln URLs"))

    timer_end(start_time, "Parameter Discovery (Active + Passive)")

def step_hakrawler_crawl(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping crawling (intensity: light)")
        return

    print_step("🕸️ Crawling with Hakrawler")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    raw_dir = os.path.join(domain_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    hakrawler_raw = os.path.join(raw_dir, "hakrawler_raw.txt")
    hakrawler_clean = os.path.join(domain_dir, "hakrawler_cleaned.txt")
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    crawled_urls = set()

    if not shutil.which("hakrawler"):
        logger.warning("[hakrawler] Not installed. Skipping.")
        alert("Hakrawler", ["Binary not found in PATH"])
        context.setdefault("failures", []).append(("Hakrawler", "Binary missing"))
        return

    try:
        with open(hakrawler_raw, "w", encoding="utf-8") as fout:
            run_command(["hakrawler", "-u", f"https://{domain}", "-depth", "3"], timeout=300, error_log=error_log, stdout=fout)

        if os.path.isfile(hakrawler_raw):
            with open(hakrawler_raw, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url.startswith("http"):
                        crawled_urls.add(url)

        context["hakrawler_urls"] = sorted(crawled_urls)

        if crawled_urls:
            with open(hakrawler_clean, "w", encoding="utf-8") as f:
                f.write("# Cleaned Hakrawler URLs\n")
                for url in sorted(crawled_urls):
                    f.write(url + "\n")
            with open(all_urls_file, "a", encoding="utf-8") as f:
                for url in sorted(crawled_urls):
                    f.write(url + "\n")
        else:
            with open(hakrawler_clean, "w", encoding="utf-8") as f:
                f.write("No URLs found.\n")
            alert("Hakrawler", ["No URLs discovered during crawl"])
            context.setdefault("failures", []).append(("Hakrawler", "0 URLs"))

        print_found("Hakrawler URLs", len(crawled_urls))

    except Exception as e:
        alert_error(f"Hakrawler crawl failed: {e}", error_log)
        context.setdefault("failures", []).append(("Hakrawler", str(e)))

    timer_end(start, "Hakrawler crawling")

def step_dig_dns(domain, config, context):
    print_step("🔎 Gathering DNS records with dig")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    dns_out = os.path.join(domain_dir, "dns_records.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    records = []
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA"]

    try:
        with open(dns_out, "w", encoding="utf-8") as fout:
            for rtype in record_types:
                try:
                    result = subprocess.run(
                        ["dig", "+short", domain, rtype],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    lines = result.stdout.strip().splitlines()
                    if lines:
                        records.extend(lines)
                        fout.write(f"\n;; {rtype} RECORDS\n")
                        fout.write("\n".join(lines) + "\n")
                except Exception as e:
                    msg = f"[dig] Failed for {rtype} record: {e}"
                    logger.warning(msg)
                    with open(error_log, "a", encoding="utf-8") as ferr:
                        ferr.write(msg + "\n")
                    context["failures"] = context.get("failures", []) + [(f"Dig {rtype}", str(e))]

        if records:
            context["dns_records"] = sorted(set(records))
            print_found("DNS Records", len(records), len(set(records)))
            alert("DNS Records", list(set(records))[:10])
        else:
            context["dns_records"] = []
            with open(dns_out, "a", encoding="utf-8") as fout:
                fout.write("No DNS records found.\n")
            logger.info("[dig] No DNS records found.")
            alert("DNS", ["No DNS records found"])
            context["failures"] = context.get("failures", []) + [("DNS", "No records found")]

    except Exception as e:
        alert_error(f"[dig] DNS enumeration failed: {e}", error_log)
        context["failures"] = context.get("failures", []) + [("Dig", str(e))]

    timer_end(start, "DNS Enumeration")

def step_naabu_ports(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") != "deep":
        print_step("⏭️ Skipping port scan (requires deep intensity)")
        return

    print_step("🚪 Scanning open ports with Naabu")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    naabu_out = os.path.join(domain_dir, "naabu_ports.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    ports = set()

    if not shutil.which("naabu"):
        alert("Naabu", ["Binary not found in PATH"])
        context.setdefault("failures", []).append(("Naabu", "Binary missing"))
        return

    try:
        port_range = "1-65535" if config.get("intensity") == "deep" else "80,443,8080,8443"
        cmd = ["naabu", "-host", domain, "-o", naabu_out, "-silent", "-p", port_range, "-rate", "500"]
        run_command(cmd, timeout=300, error_log=error_log)

        if os.path.isfile(naabu_out):
            with open(naabu_out, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) == 2 and parts[1].isdigit():
                        ports.add(parts[1])

        context["open_ports"] = sorted(ports)

        if ports:
            print_found("Open Ports", len(ports))
            alert("Open Ports", sorted(ports))
        else:
            logger.info("No open ports detected by Naabu.")
            with open(naabu_out, "w", encoding="utf-8") as f:
                f.write("No open ports detected.\n")
            context.setdefault("failures", []).append(("Naabu", "0 ports"))

    except Exception as e:
        alert_error(f"Naabu failed: {e}", error_log)
        context.setdefault("failures", []).append(("Naabu", str(e)))

    timer_end(start, "Port scan")

def step_gf_patterns(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") != "deep":
        print_step("⏭️ Skipping GF pattern scan (requires deep intensity)")
        return

    print_step("📌 Searching GF patterns in URLs")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    urls_file = os.path.join(domain_dir, "all_urls.txt")
    gf_out = os.path.join(domain_dir, "gf_patterns.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    vuln_lines = set()
    patterns = ["xss", "sqli", "redirect", "ssti", "rce", "idor", "lfi", "rfi", "debug_logic"]

    if not shutil.which("gf"):
        alert("GF", ["Binary not found in PATH"])
        context.setdefault("failures", []).append(("GF", "Binary missing"))
        return

    if not os.path.isfile(urls_file) or os.path.getsize(urls_file) == 0:
        logger.warning("No URLs to scan with GF.")
        return

    try:
        with open(gf_out, "w", encoding="utf-8") as fout:
            for pattern in patterns:
                try:
                    result = subprocess.run(
                        ["gf", pattern],
                        stdin=open(urls_file, "r", encoding="utf-8"),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.stdout:
                        lines = result.stdout.strip().splitlines()
                        vuln_lines.update(lines)
                        fout.write(f"\n## Pattern: {pattern.upper()}\n")
                        fout.write("\n".join(lines) + "\n")
                except Exception as e:
                    alert_error(f"GF pattern {pattern} failed: {e}", error_log)
                    context.setdefault("failures", []).append((f"GF {pattern}", str(e)))

        context["gf_vulns"] = sorted(vuln_lines)

        if vuln_lines:
            print_found("GF Matches", len(vuln_lines))
            alert("GF Matches", list(vuln_lines)[:10])
        else:
            with open(gf_out, "w", encoding="utf-8") as f:
                f.write("No patterns matched.\n")

    except Exception as e:
        alert_error(f"GF pattern matching failed: {e}", error_log)
        context.setdefault("failures", []).append(("GF", str(e)))

    timer_end(start, "GF pattern matching")

def step_scan_sensitive_files(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping sensitive file scan (intensity: light)")
        return

    print_step("🔐 Scanning for sensitive files")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    wayback_file = context.get('wayback_urls', os.path.join(domain_dir, "waybackurls.txt"))
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    sensitive_file = os.path.join(domain_dir, "sensitive_files.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    sensitive_urls = set()

    sensitive_patterns = [
        r"\.env$", r"\.bak$", r"\.sql$", r"\.config$", r"\.json$", r"\.log$",
        r"\.git/", r"wp-config\.php$", r"admin/", r"backup/", r"token", r"secret", r"credentials", r"\.key$", r"\.crt$"
    ]
    sensitive_regex = re.compile("|".join(sensitive_patterns), re.I)
    keywords = ["password", "secret", "token", "auth", "key", "db", "access"]

    urls = []
    for file in [wayback_file, all_urls_file]:
        if os.path.isfile(file) and os.path.getsize(file) > 0:
            with open(file, "r", encoding="utf-8") as f:
                urls += [line.strip() for line in f if sensitive_regex.search(line)]

    if urls:
        try:
            with open(sensitive_file, "w", encoding="utf-8") as fout:
                found = False
                for url in urls:
                    is_live, has_sensitive = url_check(url, keywords)
                    if is_live:
                        found = True
                        label = "[SENSITIVE]" if has_sensitive else "[LIVE]"
                        fout.write(f"{label} {url}\n")
                        if has_sensitive:
                            sensitive_urls.add(url)
                    random_delay(config.get("intensity"))
                if not found:
                    fout.write("No sensitive files or links found.\n")
        except Exception as e:
            alert_error(f"Sensitive scan failed: {e}", error_log)
            context.setdefault("failures", []).append(("Sensitive Files", str(e)))
    else:
        with open(sensitive_file, "w", encoding="utf-8") as f:
            f.write("No URLs for sensitive file scanning.\n")
        logger.warning("No URLs for sensitive file scan.")

    context["sensitive_urls"] = sorted(sensitive_urls)
    print_found("Sensitive Files", len(sensitive_urls))

    timer_end(start, "Sensitive file scanning")
def step_scan_juicy_info(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") == "light":
        print_step("⏭️ Skipping juicy info scan (intensity: light)")
        return

    print_step("🍯 Scanning for juicy info")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    wayback_file = context.get('wayback_urls', os.path.join(domain_dir, "waybackurls.txt"))
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    juicy_file = os.path.join(domain_dir, "juicy_info.txt")
    js_dir = os.path.join(domain_dir, "js_files")
    os.makedirs(js_dir, exist_ok=True)
    error_log = os.path.join(domain_dir, "errors.log")
    juicy_urls = set()

    pattern_keywords = [
        r"api[_-]?key", r"token", r"password", r"secret_key", r"access[_-]?key",
        r"aws[_-]?key", r"auth[_-]?token", r"credential", r"s3\.amazonaws\.com",
        r"firebase", r"client[_-]?id", r"client_secret", r"oauth[_-]?access_token",
        r"database[_-]?url", r"mongodb://", r"mysql://", r"postgres://", r"slack_token",
        r"bearer[_-]?token", r"jwt="
    ]
    false_positive = re.compile(r"csrf_token|xsrf_token|nonce|form_token", re.I)
    pattern_regex = re.compile("|".join(pattern_keywords), re.I)

    urls = []
    for url_file in [wayback_file, all_urls_file]:
        if os.path.isfile(url_file) and os.path.getsize(url_file) > 0:
            try:
                with open(url_file, "r", encoding="utf-8") as fin:
                    urls.extend(line.strip() for line in fin if pattern_regex.search(line))
            except Exception as exc:
                alert_error(f"Error reading {url_file}", error_log)
                context.setdefault("failures", []).append(("Juicy Info Read", str(exc)))

    if urls:
        try:
            with open(juicy_file, "w", encoding="utf-8") as fout:
                for url in urls:
                    if false_positive.search(url):
                        continue
                    is_live, _ = url_check(url)
                    if is_live:
                        juicy_urls.add(url)
                        fout.write(f"[LIVE] {url}\n")
                        if url.endswith(('.js', '.jsx')):
                            try:
                                r = requests.get(url, headers={"User-Agent": get_random_user_agent()}, timeout=5, verify=False)
                                if r.status_code == 200:
                                    js_name = f"js_{hashlib.md5(url.encode()).hexdigest()}.js"
                                    with open(os.path.join(js_dir, js_name), "w", encoding="utf-8") as fj:
                                        fj.write(r.text)
                            except Exception as e:
                                logger.debug(f"JS download failed: {url} - {e}")
                    random_delay(config.get("intensity"))
                if not juicy_urls:
                    fout.write("No juicy info found.\n")
        except Exception as e:
            alert_error(f"Juicy info scan failed: {e}", error_log)
            context.setdefault("failures", []).append(("Juicy Info", str(e)))
    else:
        with open(juicy_file, "w", encoding="utf-8") as f:
            f.write("No juicy URLs to scan.\n")

    context["juicy_urls"] = sorted(juicy_urls)
    print_found("Juicy Info", len(juicy_urls))
    timer_end(start, "Juicy info scan")


def httprobe_is_live(url):
    try:
        # Run httprobe with concurrency 10, check if URL is alive
        proc = subprocess.run(
            ['httprobe', '-c', '10'],
            input=url.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        live_urls = proc.stdout.decode().splitlines()
        # Match URL ignoring trailing slash
        return any(url.rstrip('/') == live.rstrip('/') for live in live_urls)
    except Exception as e:
        logger.debug(f"httprobe error on {url}: {e}")
        return False
        

def httprobe_is_live(url):
    try:
        # Run httprobe with concurrency 10, check if URL is alive
        proc = subprocess.run(
            ['httprobe', '-c', '10'],
            input=url.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        live_urls = proc.stdout.decode().splitlines()
        # Match URL ignoring trailing slash
        return any(url.rstrip('/') == live.rstrip('/') for live in live_urls)
    except Exception as e:
        logger.debug(f"httprobe error on {url}: {e}")
        return False

def url_check(url, keywords=None):
    try:
        is_live = httprobe_is_live(url)
        if not is_live:
            return False, False
        if not keywords:
            return True, False

        headers = {"User-Agent": get_random_user_agent()}
        proxy = get_proxy() or {}

        r = requests.get(
            url,
            headers=headers,
            proxies=proxy,
            timeout=8,
            allow_redirects=False,
            verify=False
        )
        body = r.text.lower()
        has_sensitive = any(kw.lower() in body for kw in keywords)
        return True, has_sensitive
    except Exception as exc:
        logger.debug(f"url_check error on {url}: {exc}")
        return False, False

def url_check(url, keywords=None):
    try:
        is_live = httprobe_is_live(url)
        if not is_live:
            return False, False
        if not keywords:
            return True, False

        headers = {"User-Agent": get_random_user_agent()}
        proxy = get_proxy() or {}

        r = requests.get(
            url,
            headers=headers,
            proxies=proxy,
            timeout=8,
            allow_redirects=False,
            verify=False
        )
        body = r.text.lower()
        has_sensitive = any(kw.lower() in body for kw in keywords)
        return True, has_sensitive
    except Exception as exc:
        logger.debug(f"url_check error on {url}: {exc}")
        return False, False

def step_advanced_xss(domain, config, context):
    if context.get("skip", False):
        return
    if config.get("intensity") != "deep":
        print_step("⏭️ Skipping XSS scan (requires deep intensity)")
        return

    print_step("🔬 Scanning for XSS (Dalfox + XSStrike)")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    dalfox_file = os.path.join(domain_dir, "dalfox.txt")
    xsstrike_file = os.path.join(domain_dir, "xsstrike.txt")
    live_param_urls_file = os.path.join(domain_dir, "live_param_urls.txt")
    xss_results = []

    # Dalfox
    if config.get("dalfox", False) and os.path.isfile(live_param_urls_file) and os.path.getsize(live_param_urls_file) > 0:
        try:
            random_delay(config.get("intensity"))
            stdout = run_command(
                [
                    "dalfox", "file", live_param_urls_file,
                    "--output", dalfox_file,
                    "--user-agent", get_random_user_agent(),
                    "--delay", "500", "--timeout", "5", "--waf-evasion"
                ],
                timeout=500,
                error_log=error_log,
                capture_output=True
            )
            if stdout:
                with open(dalfox_file, "w", encoding="utf-8") as f:
                    f.write(stdout)
                xss_results.append(dalfox_file)
        except Exception as e:
            alert_error(f"Dalfox failed: {e}", error_log)
            context.setdefault("failures", []).append(("Dalfox", str(e)))
    else:
        with open(dalfox_file, "w", encoding="utf-8") as f:
            f.write("Dalfox skipped (missing input or disabled).\n")

    # XSStrike
    if config.get("xsstrike", False):
        try:
            cmd = [
                "xsstrike", "-u", f"https://{domain}",
                "--log-file", xsstrike_file,
                "--headers", f"User-Agent: {get_random_user_agent()}",
                "--encode", "--timeout", "5"
            ]
            proxy = get_proxy()
            if proxy:
                cmd.extend(["--proxy", proxy.get("http", "")])

            random_delay(config.get("intensity"))
            stdout = run_command(cmd, timeout=300, error_log=error_log, capture_output=True)

            if stdout:
                with open(xsstrike_file, "w", encoding="utf-8") as f:
                    f.write(stdout)
                xss_results.append(xsstrike_file)
        except Exception as e:
            alert_error(f"XSStrike failed: {e}", error_log)
            context.setdefault("failures", []).append(("XSStrike", str(e)))
    else:
        with open(xsstrike_file, "w", encoding="utf-8") as f:
            f.write("XSStrike skipped (disabled).\n")

    context["xss"] = xss_results
    print_found("XSS Tools Output", len(xss_results))
    timer_end(start_time, "XSS Scanning")
def step_nuclei_scan(domain, config, context):
    if context.get("skip", False):
        return

    print_step("🧬 Scanning with Nuclei")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    live_param_urls_file = os.path.join(domain_dir, "live_param_urls.txt")
    nuclei_out = os.path.join(domain_dir, "nuclei.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    results = []

    if not shutil.which("nuclei"):
        alert("Nuclei", ["Binary not found"])
        context.setdefault("failures", []).append(("Nuclei", "Binary missing"))
        return

    if not os.path.isfile(live_param_urls_file) or os.path.getsize(live_param_urls_file) == 0:
        logger.warning("Nuclei input missing.")
        with open(nuclei_out, "w", encoding="utf-8") as f:
            f.write("No input for Nuclei scan.\n")
        return

    try:
        default_template_path = os.path.expanduser("~/.local/nuclei-templates/")
        template_path = config.get("nuclei_template_path", default_template_path)

        cmd = [
            "nuclei", "-l", live_param_urls_file, "-o", nuclei_out,
            "-silent", "-c", str(config.get("threads", 16)),
            "-H", f"User-Agent: {get_random_user_agent()}", "-rl", "30"
        ]

        if config.get("run_nuclei_full", False):
            cmd.extend(["-t", template_path])
        else:
            cmd.extend(["-tags", "cves,exposures,vulnerabilities"])

        run_command(cmd, timeout=300, error_log=error_log)

        if os.path.isfile(nuclei_out):
            with open(nuclei_out, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        results.append(line.strip())

        context["nuclei_vulns"] = results

        if results:
            print_found("Nuclei Vulns", len(results))
            alert("Nuclei Findings", results[:10])
        else:
            with open(nuclei_out, "w", encoding="utf-8") as f:
                f.write("No vulnerabilities found.\n")
            logger.info("Nuclei found no issues.")

    except Exception as e:
        alert_error(f"Nuclei failed: {e}", error_log)
        context.setdefault("failures", []).append(("Nuclei", str(e)))

    timer_end(start, "Nuclei Scanning")


def step_sqlmap(domain, config, context):
    if context.get("skip", False):
        return
    if not config.get("run_sqlmap", False):
        print_step("⏭️ SQLMap disabled in config")
        return

    print_step("🧪 Running SQLMap with advanced techniques")
    start_time = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    live_param_urls_file = os.path.join(domain_dir, "live_param_urls.txt")
    sqlmap_logs = []

    if not os.path.isfile(live_param_urls_file) or os.path.getsize(live_param_urls_file) == 0:
        alert("SQLMap", ["No live param URLs for scanning"])
        with open(error_log, "a", encoding="utf-8") as f:
            f.write("SQLMap skipped — no live param input.\n")
        return

    try:
        with open(live_param_urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        for i, url in enumerate(urls[:10]):  # Limit to 10 targets
            sqlmap_dir = os.path.join(domain_dir, f"sqlmap_{i+1}")
            os.makedirs(sqlmap_dir, exist_ok=True)
            random_delay(config.get("intensity"))

            cmd = [
                "sqlmap", "-u", url,
                "--batch",
                "--random-agent",
                "--level", "5", "--risk", "3",
                "--dbs", "--banner", "--is-dba", "--current-db", "--current-user",
                "--technique", "BEUSTQ",  # All SQLi techniques: Boolean, Error, Union, Stacked, Time, Inline
                "--tamper", "space2comment,between,randomcase,space2plus,charunicodeencode,modsecurityversioned",
                "--output-dir", sqlmap_dir,
                "--timeout", "10", "--retries", "2", "--delay", "0.5"
            ]

            proxy = get_proxy()
            if proxy:
                cmd.extend(["--proxy", proxy.get("http", "")])

            run_command(cmd, timeout=1000, error_log=error_log)
            if os.path.isdir(sqlmap_dir) and os.listdir(sqlmap_dir):
                sqlmap_logs.append(sqlmap_dir)

    except Exception as e:
        alert_error(f"SQLMap failed: {e}", error_log)
        context.setdefault("failures", []).append(("SQLMap", str(e)))

    context["sqlmap"] = sqlmap_logs
    print_found("SQLMap Logs", len(sqlmap_logs))
    if sqlmap_logs:
        alert("SQLMap Results", sqlmap_logs[:3])
    else:
        alert("SQLMap", ["No SQLi detected or tool failed."])

    timer_end(start_time, "SQL injection scan")


def step_dir_fuzz(domain, config, context):
    if context.get("skip", False):
        return

    print_step("📂 Fuzzing directories/files")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    fuzz_tool = config.get("dir_fuzz_tool", "ffuf").lower()
    wordlist = config.get("wordlist")
    fuzz_out = os.path.join(domain_dir, "dir_fuzz.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    found_dirs = set()

    if not wordlist or not os.path.isfile(wordlist):
        alert("Fuzzing", ["Wordlist not found or not configured"])
        context.setdefault("failures", []).append(("Fuzz", "Missing wordlist"))
        return

    if fuzz_tool == "ffuf":
        if not shutil.which("ffuf"):
            alert("FFUF", ["Binary not found"])
            context.setdefault("failures", []).append(("FFUF", "Binary missing"))
            return
        try:
            temp_file = os.path.join(domain_dir, "ffuf_temp.json")
            cmd = [
                "ffuf", "-u", f"https://{domain}/FUZZ",
                "-w", wordlist,
                "-mc", "200,204,301,302,307,403",
                "-t", str(config.get("threads", 20)),
                "-o", temp_file,
                "-of", "json"
            ]
            run_command(cmd, timeout=300, error_log=error_log)

            if os.path.isfile(temp_file):
                with open(temp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for result in data.get("results", []):
                        url = result.get("url")
                        status = result.get("status")
                        length = result.get("length")
                        if url and status in [200, 301, 302, 403]:
                            found_dirs.add(f"[{status}] {url} ({length} bytes)")

                os.remove(temp_file)

        except Exception as e:
            alert_error(f"FFUF fuzz failed: {e}", error_log)
            context.setdefault("failures", []).append(("FFUF", str(e)))
            return

    elif fuzz_tool == "dirsearch":
        if not shutil.which("dirsearch"):
            alert("Dirsearch", ["Binary not found"])
            context.setdefault("failures", []).append(("Dirsearch", "Binary missing"))
            return
        raw_out = os.path.join(domain_dir, "dirsearch_raw.txt")
        try:
            run_command([
                "dirsearch", "-u", f"https://{domain}",
                "-w", wordlist, "-e", "*", "-t", str(config.get("threads", 10)),
                "--plain-text-report", raw_out
            ], timeout=300, error_log=error_log)

            if os.path.isfile(raw_out):
                with open(raw_out, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("http"):
                            found_dirs.add(line.strip())

        except Exception as e:
            alert_error(f"Dirsearch failed: {e}", error_log)
            context.setdefault("failures", []).append(("Dirsearch", str(e)))
            return

    else:
        alert("Fuzzing", [f"Unknown fuzz tool: {fuzz_tool}"])
        return

    with open(fuzz_out, "w", encoding="utf-8") as f:
        for url in sorted(found_dirs):
            f.write(f"{url}\n")

    context["fuzz_dirs"] = sorted(found_dirs)
    print_found("Fuzzed Paths", len(found_dirs))
    if found_dirs:
        alert("Directory Fuzzing", list(found_dirs)[:10])
    else:
        with open(fuzz_out, "w", encoding="utf-8") as f:
            f.write("No valid directories discovered.\n")
        logger.info("No directories discovered by fuzzing.")

    timer_end(start, "Directory fuzzing")

def step_generate_report(domain, config, context):
    if context.get("skip", False):
        return

    print_step("📝 Generating final report")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    report_file = os.path.join(domain_dir, "report.html")
    error_log = os.path.join(domain_dir, "errors.log")

    try:
        generate_report(domain, config, context, report_file)
        print_step(f"📄 Report created at: {report_file}")
    except Exception as exc:
        alert_error(f"Report generation failed: {exc}", error_log)
        context.setdefault("failures", []).append(("Report", str(exc)))

    timer_end(start, "Report Generation")

def get_steps_for_intensity(intensity):
    steps = [
        step_check_dependencies,
        step_subdomain_enum,
        step_wayback_urls,
    ]
    if intensity in ["medium", "deep"]:
        steps.extend([
            step_waymore_urls,
            step_parse_param_urls,
            step_probe_param_urls,
            step_param_discovery,
            step_scan_sensitive_files,
            step_scan_juicy_info,
            step_hakrawler_crawl,
            step_nuclei_scan,
            step_dir_fuzz,
            
        ])
    if intensity == "deep":
        steps.extend([
            step_subjack_takeover,
            step_naabu_ports,
            step_gf_patterns,
            step_advanced_xss,
            step_nuclei_scan,
            step_sqlmap,
            step_dig_dns,
        ])
    steps.append(step_generate_report)
    return steps
