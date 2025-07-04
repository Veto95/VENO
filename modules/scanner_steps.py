import os
import shutil
import subprocess
import time
import logging
import random
import traceback
import re
import json
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
    message = f"\n[ALERT] {title.upper()} FOUND:\n" + "\n".join(f"- {item}" for item in data_list[:10])
    if console:
        console.print(color(message, "red", bold=True))
    else:
        print(color(message, "red", bold=True))

def alert_error(msg, error_log):
    message = f"\n[ERROR] {msg}"
    if console:
        console.print(color(message, "red", bold=True))
    else:
        print(color(message, "red", bold=True))
    try:
        os.makedirs(os.path.dirname(error_log), exist_ok=True)
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
        "light": (0.5, 1.0),
        "medium": (0.6, 1.5),
        "deep": (0.1, 1.0)
    }
    min_delay, max_delay = delays.get(intensity, delays["medium"])
    time.sleep(random.uniform(min_delay, max_delay))

def run_command(cmd, timeout, error_log, capture_output=False, stdout=None, input=None):
    os.makedirs(os.path.dirname(error_log), exist_ok=True)
    try:
        result = subprocess.run(
            cmd,
            check=True,
            timeout=timeout,
            stdout=stdout if stdout else subprocess.PIPE if capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            input=input
        )
        return result.stdout if capture_output else None
    except subprocess.TimeoutExpired as exc:
        error_msg = f"Command timed out after {timeout}s: {' '.join(cmd)}\nStderr: {exc.stderr.strip() if exc.stderr else 'N/A'}"
        alert_error(error_msg, error_log)
        logger.error(error_msg)
        return None
    except subprocess.CalledProcessError as exc:
        error_msg = f"Command failed with exit code {exc.returncode}: {' '.join(cmd)}\nStderr: {exc.stderr.strip() if exc.stderr else 'N/A'}"
        alert_error(error_msg, error_log)
        logger.error(error_msg)
        return None
    except FileNotFoundError:
        error_msg = f"Command not found: {cmd[0]}. Please ensure it's installed and in your PATH."
        alert_error(error_msg, error_log)
        logger.error(error_msg)
        return None
    except Exception as exc:
        error_msg = f"An unexpected error occurred running command {' '.join(cmd)}: {str(exc)}\nStack trace: {traceback.format_exc()}"
        alert_error(error_msg, error_log)
        logger.error(error_msg)
        return None

def normalize_domain(domain):
    parsed = urlparse(f"https://{domain}" if not domain.startswith(("http://", "https://")) else domain)
    domain = parsed.hostname or domain
    return domain.lower().strip()

def step_check_dependencies(domain, config, context):
    print_step("Checking dependencies")
    error_log = os.path.join(config.get("output_dir", "."), domain, "errors.log")
    os.makedirs(os.path.dirname(error_log), exist_ok=True)
    try:
        check_dependencies(config.get("output_dir"))
        context["dependencies"] = True
        print_step("All dependencies satisfied")
    except Exception as exc:
        error_msg = f"Dependency check failed: {str(exc)}\nStack trace: {traceback.format_exc()}"
        alert_error(error_msg, error_log)
        context.setdefault("failures", []).append(("Dependencies", str(exc)))
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
        if shutil.which("subfinder"):
            print_step("Running Subfinder...")
            random_delay(intensity)
            stdout = run_command(
                ["subfinder", "-silent", "-d", domain, "-t", str(config.get("threads", 25)), "-timeout", "300"],
                timeout=600,
                error_log=error_log,
                capture_output=True
            )
            if stdout:
                subs.update(line.strip() for line in stdout.splitlines() if line.strip())
        else:
            alert_error("Subfinder not found. Skipping subdomain enumeration with Subfinder.", error_log)
            context.setdefault("failures", []).append(("Subfinder", "Binary missing"))

        if intensity in ["medium", "deep"] and shutil.which("theHarvester"):
            print_step("Running theHarvester...")
            harvester_sources = ["crtsh", "anubis", "certspotter", "hackertarget"]
            for src in harvester_sources:
                random_delay(intensity)
                cmd = ["theHarvester", "-d", domain, "-b", src]
                output = run_command(cmd, timeout=700, error_log=error_log, capture_output=True)
                if output:
                    subs.update(re.findall(rf"[\w\-.]+\.{re.escape(domain)}", output, re.IGNORECASE))
        elif intensity in ["medium", "deep"]:
            alert_error("theHarvester not found. Skipping subdomain enumeration with theHarvester.", error_log)
            context.setdefault("failures", []).append(("the PUSH YOUR LIMITS! 🚀Harvester", "Binary missing"))

        if not subs:
            alert("Subdomain Enum", ["No subdomains found"])
            context.setdefault("failures", []).append(("Subdomain Enum", "No subs"))
        else:
            with open(all_subs_out, "w", encoding="utf-8") as f:
                for sub in sorted(subs):
                    f.write(f"{sub}\n")
            context["subdomains"] = sorted(subs)

        if subs and shutil.which("httprobe"):
            print_step("⚡ Probing with httprobe")
            retries = 3
            success = False
            for attempt in range(retries):
                try:
                    temp_sub_input = os.path.join(domain_dir, "temp_httprobe_input.txt")
                    with open(temp_sub_input, "w", encoding="utf-8") as f:
                        f.write("\n".join(subs))

                    probe_cmd = ["httprobe", "-c", "100", "-t", "15000", "-p", "http:80,https:443"]
                    probe = subprocess.Popen(
                        probe_cmd,
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore"
                    )
                    with open(temp_sub_input, "r", encoding="utf-8") as f_in:
                        out, err = probe.communicate(input=f_in.read(), timeout=300)

                    if err:
                        logger.warning(f"httprobe attempt {attempt+1}/{retries} stderr: {err.strip()}")
                        with open(error_log, "a", encoding="utf-8") as ef:
                            ef.write(f"[httprobe] Attempt {attempt+1}/{retries} stderr: {err.strip()}\n")
                    if probe.returncode == 0:
                        for line in out.splitlines():
                            host = urlparse(line.strip()).netloc
                            if host:
                                live_subs.add(host)
                        success = True
                        break
                    else:
                        logger.warning(f"httprobe attempt {attempt+1}/{retries} failed with return code {probe.returncode}")
                        if attempt < retries - 1:
                            time.sleep(5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"httprobe attempt {attempt+1}/{retries} timed out.")
                    if attempt < retries - 1:
                        time.sleep(5)
                except Exception as exc:
                    logger.warning(f"httprobe attempt {attempt+1}/{retries} failed: {exc}")
                    with open(error_log, "a", encoding="utf-8") as ef:
                        ef.write(f"[httprobe] Attempt {attempt+1}/{retries} error: {exc}\n")
                    if attempt < retries - 1:
                        time.sleep(5)
                finally:
                    if os.path.exists(temp_sub_input):
                        os.remove(temp_sub_input)

            if not success and shutil.which("httping"):
                print_step("⚡ httprobe failed, falling back to httping (slower)")
                for sub in subs:
                    try:
                        for proto in ["https", "http"]:
                            cmd = ["httping", "-c", "1", "-t", "5", f"{proto}://{sub}"]
                            result = run_command(cmd, timeout=100, error_log=error_log, capture_output=True)
                            if result and ("connected to" in result.lower() or "200 ok" in result.lower()):
                                live_subs.add(f"{proto}://{sub}".split('//')[1])
                                break
                    except Exception as exc:
                        logger.warning(f"httping failed for {sub}: {exc}")
                        alert_error(f"httping fallback failed for {sub}: {exc}", error_log)
                        context.setdefault("failures", []).append(("httping", str(exc)))
        elif subs:
            alert_error("httprobe not found. Skipping live subdomain probing.", error_log)
            context.setdefault("failures", []).append(("httprobe", "Binary missing"))

        if not live_subs:
            alert_error("No live subdomains found", error_log)
            context.setdefault("failures", []).append(("httprobe", "No live subdomains"))

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
    print_step("🎯 Checking for takeover with Subjack")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    error_log = os.path.join(domain_dir, "errors.log")
    subs = context.get("subdomains", [])
    if not subs:
        alert("Subjack", ["Missing subdomains from previous step. Skipping."])
        context.setdefault("failures", []).append(("Subjack", "No input subs"))
        return

    if not config.get("run_subjack", False):
        print_step("⏭️ Subjack disabled in config")
        return

    if not shutil.which("subjack"):
        alert("Subjack", ["Binary not found in PATH. Skipping."])
        context.setdefault("failures", []).append(("Subjack", "Binary missing"))
        return

    input_file = os.path.join(domain_dir, "subjack_input.txt")
    output_file = os.path.join(domain_dir, "subjack_takeover.txt")
    takeovers = set()

    try:
        with open(input_file, "w", encoding="utf-8") as f:
            f.write("\n".join(subs))

        cmd = [
            "subjack", "-w", input_file, "-o", output_file,
            "-t", str(config.get("threads", 20)), "-timeout", "60", "-ssl"
        ]
        run_command(cmd, timeout=900, error_log=error_log)

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
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
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
        if shutil.which("waybackurls"):
            print_step("Running waybackurls...")
            random_delay(intensity)
            stdout = run_command(["waybackurls", domain], timeout=3000, error_log=error_log, capture_output=True)
            if stdout:
                with open(wayback_file, "w", encoding="utf-8") as f:
                    f.write(stdout)
                urls.update(line.strip() for line in stdout.splitlines() if line.strip())
        else:
            alert_error("waybackurls not found. Skipping waybackurls.", error_log)
            context.setdefault("failures", []).append(("waybackurls", "Binary missing"))

        if (not urls or not shutil.which("waybackurls")) and config.get("gau", True) and shutil.which("gau"):
            print_step("🔁 Falling back to gau...")
            random_delay(intensity)
            stdout = run_command(["gau", domain, "--threads", str(config.get("threads", 10)), "-timeout", "60"], timeout=3000, error_log=error_log, capture_output=True)
            if stdout:
                with open(gau_file, "w", encoding="utf-8") as f:
                    f.write(stdout)
                urls.update(line.strip() for line in stdout.splitlines() if line.strip())
                context["wayback_urls"] = gau_file
            else:
                context["wayback_urls"] = wayback_file

        if urls:
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
    if not config.get("run_waymore", False):
        print_step("⏭️ Waymore disabled in config")
        return

    print_step("📜 Gathering URLs with Waymore")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    intensity = config.get("intensity", "medium")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    waymore_file = os.path.join(domain_dir, "waymore_urls.txt")
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    urls = set()
    random_delay(intensity)

    if not shutil.which("waymore"):
        alert_error("Waymore not found. Skipping Waymore scan.", error_log)
        context.setdefault("failures", []).append(("Waymore", "Binary missing"))
        return

    stdout = run_command(
        ["waymore", "-i", domain, "-oU", waymore_file, "-mode", "U", "-f", "json"],
        timeout=1200,
        error_log=error_log,
        capture_output=True
    )

    if os.path.isfile(waymore_file):
        try:
            with open(waymore_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if "url" in data:
                            urls.add(data["url"])
                    except json.JSONDecodeError:
                        urls.add(line.strip())
        except Exception as e:
            alert_error(f"Error reading Waymore output file: {e}", error_log)
    elif stdout:
        for line in stdout.splitlines():
            try:
                data = json.loads(line.strip())
                if "url" in data:
                    urls.add(data["url"])
            except json.JSONDecodeError:
                urls.add(line.strip())

    if urls:
        with open(all_urls_file, "a", encoding="utf-8") as f:
            for url in sorted(urls):
                f.write(url + "\n")

        context.setdefault("urls", []).extend(sorted(urls))
        print_found("Waymore URLs", len(urls))
    else:
        logger.warning("[VENO] ❗ Waymore found no URLs")
        alert("Waymore", ["No URLs extracted"])
        context.setdefault("failures", []).append(("Waymore", "No URLs found"))

    timer_end(start, "Waymore URL Collection")

def step_assetfinder_crawl(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🕷️ Enumerating assets with Assetfinder")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    assetfinder_out = os.path.join(domain_dir, "assetfinder.txt")
    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    domain = normalize_domain(domain)
    urls = set()

    try:
        if not shutil.which("assetfinder"):
            alert("Assetfinder", ["Binary not found in PATH"])
            context.setdefault("failures", []).append(("Assetfinder", "Binary missing"))
            return

        cmd = ["assetfinder", "--subs-only", domain]
        proxy = get_proxy()
        if proxy:
            cmd.extend(["--proxy", proxy.get("http", "")])

        retries = 3
        for attempt in range(retries):
            result = run_command(cmd, timeout=600, error_log=error_log, capture_output=True)
            if result:
                for line in result.splitlines():
                    line = line.strip()
                    if line and re.match(rf"[\w\-.]+\.{re.escape(domain)}", line):
                        urls.add(f"https://{line}")
                break
            else:
                logger.warning(f"assetfinder attempt {attempt+1}/{retries} failed")
                if attempt < retries - 1:
                    time.sleep(5)

        if urls:
            with open(assetfinder_out, "w", encoding="utf-8") as f:
                for url in sorted(urls):
                    f.write(f"{url}\n")
            with open(all_urls_file, "a", encoding="utf-8") as f:
                for url in sorted(urls):
                    f.write(f"{url}\n")
            print_found("Assetfinder URLs", len(urls))
            context.setdefault("urls", []).extend(sorted(urls))
        else:
            logger.warning("Assetfinder returned no URLs.")
            with open(assetfinder_out, "w", encoding="utf-8") as f:
                f.write("No URLs found by assetfinder.\n")
            context.setdefault("failures", []).append(("Assetfinder", "0 URLs"))
    except Exception as e:
        alert_error(f"Assetfinder crawl failed: {e}", error_log)
        context.setdefault("failures", []).append(("Assetfinder", str(e)))

    timer_end(start, "Assetfinder Crawl")

def step_parse_param_urls(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🔎 Parsing URLs for parameters and dynamic endpoints")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    param_urls_file = os.path.join(domain_dir, "param_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    param_urls = set()

    try:
        if not os.path.isfile(all_urls_file) or os.path.getsize(all_urls_file) == 0:
            alert("Parameter Parsing", ["No URLs found in all_urls.txt. Skipping."])
            context.setdefault("failures", []).append(("Parameter Parsing", "No input URLs"))
            with open(param_urls_file, "w", encoding="utf-8") as f:
                f.write("No URLs available for parameter parsing.\n")
            return

        param_pattern = re.compile(r"\?.+=.+|\.(php|asp|aspx|jsp)$", re.I)
        with open(all_urls_file, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if url and param_pattern.search(url):
                    param_urls.add(url)

        if param_urls:
            with open(param_urls_file, "w", encoding="utf-8") as f:
                for url in sorted(param_urls):
                    f.write(f"{url}\n")
            context["param_urls"] = sorted(param_urls)
            print_found("Parameter URLs", len(param_urls))
            alert("Parameter URLs", list(param_urls)[:10])
        else:
            logger.warning("No URLs with parameters or dynamic endpoints found.")
            with open(param_urls_file, "w", encoding="utf-8") as f:
                f.write("No URLs with parameters or dynamic endpoints found.\n")
            context.setdefault("failures", []).append(("Parameter Parsing", "No param URLs"))

    except Exception as e:
        alert_error(f"Parameter parsing failed: {e}", error_log)
        context.setdefault("failures", []).append(("Parameter Parsing", str(e)))

    timer_end(start, "Parameter URL Extraction")

def step_probe_param_urls(domain, config, context):
    if context.get("skip", False):
        return
    print_step("⚡ Probing parameter URLs with httprobe")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    param_urls_file = os.path.join(domain_dir, "param_urls.txt")
    live_param_urls_file = os.path.join(domain_dir, "live_param_urls.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    live_urls = set()

    try:
        if not shutil.which("httprobe"):
            alert("httprobe", ["Binary not found in PATH. Skipping parameter URL probing."])
            context.setdefault("failures", []).append(("httprobe", "Binary missing"))
            return

        if not os.path.isfile(param_urls_file) or os.path.getsize(param_urls_file) == 0:
            alert("Parameter Probing", ["No parameter URLs found. Skipping."])
            context.setdefault("failures", []).append(("Parameter Probing", "No input URLs"))
            with open(live_param_urls_file, "w", encoding="utf-8") as f:
                f.write("No parameter URLs available for probing.\n")
            return

        with open(param_urls_file, "r", encoding="utf-8") as f:
            param_urls = [line.strip() for line in f if line.strip()]

        temp_input = os.path.join(domain_dir, "temp_probe_param_input.txt")
        with open(temp_input, "w", encoding="utf-8") as f:
            f.write("\n".join(param_urls))

        retries = 3
        success = False
        for attempt in range(retries):
            try:
                probe_cmd = ["httprobe", "-c", str(config.get("threads", 100)), "-t", "15000", "-p", "http:80,https:443"]
                probe = subprocess.Popen(
                    probe_cmd,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore"
                )
                with open(temp_input, "r", encoding="utf-8") as f_in:
                    out, err = probe.communicate(input=f_in.read(), timeout=300)

                if err:
                    logger.warning(f"httprobe attempt {attempt+1}/{retries} stderr: {err.strip()}")
                    with open(error_log, "a", encoding="utf-8") as ef:
                        ef.write(f"[httprobe] Attempt {attempt+1}/{retries} stderr: {err.strip()}\n")
                if probe.returncode == 0:
                    live_urls.update(line.strip() for line in out.splitlines() if line.strip())
                    success = True
                    break
                else:
                    logger.warning(f"httprobe attempt {attempt+1}/{retries} failed with return code {probe.returncode}")
                    if attempt < retries - 1:
                        time.sleep(5)
            except subprocess.TimeoutExpired:
                logger.warning(f"httprobe attempt {attempt+1}/{retries} timed out.")
                if attempt < retries - 1:
                    time.sleep(5)
            except Exception as exc:
                logger.warning(f"httprobe attempt {attempt+1}/{retries} failed: {exc}")
                with open(error_log, "a", encoding="utf-8") as ef:
                    ef.write(f"[httprobe] Attempt {attempt+1}/{retries} error: {exc}\n")
                if attempt < retries - 1:
                    time.sleep(5)
            finally:
                if os.path.exists(temp_input):
                    os.remove(temp_input)

        if live_urls:
            with open(live_param_urls_file, "w", encoding="utf-8") as f:
                for url in sorted(live_urls):
                    f.write(f"{url}\n")
            context["live_param_urls"] = sorted(live_urls)
            print_found("Live Parameter URLs", len(live_urls))
            alert("Live Parameter URLs", list(live_urls)[:10])
        else:
            logger.warning("No live parameter URLs found.")
            with open(live_param_urls_file, "w", encoding="utf-8") as f:
                f.write("No live parameter URLs found.\n")
            context.setdefault("failures", []).append(("Parameter Probing", "No live URLs"))

    except Exception as e:
        alert_error(f"Parameter URL probing failed: {e}", error_log)
        context.setdefault("failures", []).append(("Parameter Probing", str(e)))

    timer_end(start, "Parameter URL Probing")

def step_param_discovery(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🔎 Passive Param Discovery with uro")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    uro_out = os.path.join(domain_dir, "uro_params.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    param_urls = set()

    try:
        if not shutil.which("uro"):
            alert("uro", ["Binary not found in PATH"])
            context.setdefault("failures", []).append(("uro", "Binary missing"))
            return

        if os.path.isfile(all_urls_file) and os.path.getsize(all_urls_file) > 0:
            with open(all_urls_file, "r", encoding="utf-8") as f_in:
                input_data = f_in.read()

            result = run_command(
                ["uro"],
                timeout=300,
                error_log=error_log,
                capture_output=True,
                input=input_data
            )
            if result:
                param_urls.update(line.strip() for line in result.splitlines() if line.strip())
                with open(uro_out, "w", encoding="utf-8") as f:
                    for url in sorted(param_urls):
                        f.write(f"{url}\n")
            else:
                logger.warning("uro returned no URLs")
                with open(uro_out, "w", encoding="utf-8") as f:
                    f.write("No URLs found by uro.\n")
        else:
            logger.warning("No all_urls.txt available or it's empty for uro input")
            with open(uro_out, "w", encoding="utf-8") as f:
                f.write("all_urls.txt missing or empty.\n")
            alert("uro", ["all_urls.txt missing or empty"])
            context.setdefault("failures", []).append(("uro", "Missing input"))

        context["param_urls"] = sorted(param_urls)
        print_found("uro Param URLs", len(param_urls))

    except Exception as e:
        alert_error(f"uro param discovery failed: {e}", error_log)
        context.setdefault("failures", []).append(("uro", str(e)))

    timer_end(start, "Passive Param Discovery")

def step_extract_juicy_info(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🍯 Extracting juicy info from uro URLs")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    uro_params_file = os.path.join(domain_dir, "uro_params.txt")
    juicy_file = os.path.join(domain_dir, "juicy_info.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    pattern_keywords = [
        r"api[_-]?key", r"token", r"password", r"secret_key", r"access[_-]?key",
        r"aws[_-]?key", r"auth[_-]?token", r"credential", r"s3\.amazonaws\.com",
        r"firebase", r"client[_-]?id", r"client_secret", r"oauth[_-]?access_token",
        r"database[_-]?url", r"mongodb://", r"mysql://", r"postgres://", r"slack_token",
        r"bearer[_-]?token", r"jwt=", r"x-api-key", r"shopify[_-]?token", r"stripe[_-]?key",
        r"access[_-]?token", r"authorization=[a-zA-Z0-9-_]+", r"x-amz-signature", r"x-goog-signature",
        r"x-rapidapi-key", r"github[_-]?token", r"gcp[_-]?key", r"cloudinary[_-]?url",
        r"webhook[_-]?url", r"zoom[_-]?token", r"heroku[_-]?key", r"netlify[_-]?token",
        r"digitalocean[_-]?token", r"bitbucket[_-]?key", r"twilio[_-]?auth[_-]?token",
        r"key=[a-zA-Z0-9_-]+", r"secret=[a-zA-Z0-9_-]+", r"auth=[a-zA-Z0-9_-]+"
    ]
    pattern_regex = re.compile("|".join(pattern_keywords), re.I)
    false_positive = re.compile(r"csrf_token|xsrf_token|nonce|form_token", re.I)

    urls = context.get("param_urls", [])
    if not urls:
        logger.warning("No uro URLs available for juicy info extraction in context. Checking file.")
        if os.path.isfile(uro_params_file) and os.path.getsize(uro_params_file) > 0:
            with open(uro_params_file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
            if urls:
                logger.debug(f"Loaded {len(urls)} URLs from uro_params.txt as fallback")
                context["param_urls"] = sorted(urls)
            else:
                logger.warning("uro_params.txt is empty or contains no URLs.")
                context["juicy_urls"] = []
                with open(juicy_file, "w", encoding="utf-8") as f:
                    f.write("No uro URLs available for juicy info extraction.\n")
                timer_end(start, "Juicy Info Extraction")
                return
        else:
            logger.warning("No uro_params.txt file found or it's empty.")
            context["juicy_urls"] = []
            with open(juicy_file, "w", encoding="utf-8") as f:
                f.write("No uro URLs available for juicy info extraction.\n")
            timer_end(start, "Juicy Info Extraction")
            return

    juicy_urls = [url for url in urls if pattern_regex.search(url) and not false_positive.search(url)]
    logger.debug(f"Found {len(juicy_urls)} juicy URLs from uro output")

    with open(juicy_file, "w", encoding="utf-8") as f:
        for url in juicy_urls:
            f.write(f"{url}\n")

    context["juicy_urls"] = juicy_urls
    print_found("Juicy Info", len(juicy_urls))
    timer_end(start, "Juicy Info Extraction")

def step_extract_sensitive_files(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🔐 Extracting sensitive files from URLs")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    sensitive_file = os.path.join(domain_dir, "sensitive_files.txt")
    error_log = os.path.join(domain_dir, "errors.log")

    sensitive_patterns = [
        r"\.env$", r"\.bak$", r"\.sql$", r"\.config$", r"\.json$", r"\.log$",
        r"\.git/", r"wp-config\.php$", r"admin/", r"backup/", r"token", r"secret", r"credentials", r"\.key$", r"\.crt$",
        r"\.ini$", r"\.xml$", r"\.yml$", r"\.yaml$", r"\.DS_Store$", r"id_rsa$", r"\.pem$", r"/debug", r"dump", r"\.cache$",
        r"\.zip$", r"\.rar$", r"\.tar\.gz$", r"\.7z$", r"backup", r"/old/", r"/private/", r"/tmp/", r"passwords", r"userlist",
        r"database", r"\.bakup$", r"\.db$", r"phpinfo\.php", r"test\.php", r"info\.php", r"config\.php", r"settings\.php",
        r"web\.config", r"robots\.txt", r"sitemap\.xml", r"crossdomain\.xml", r"clientaccesspolicy\.xml", r"swagger\.json",
        r"api-docs\.json", r"graphql", r"adminer", r"phpmyadmin", r"phpPgAdmin", r"test\.txt", r"debug\.log", r"error\.log",
        r"access\.log", r"install\.log", r"install\.php", r"setup\.php", r"update\.php", r"upgrade\.php", r"composer\.json",
        r"package\.json", r"yarn\.lock", r"npm-debug\.log", r"server\.log", r"application\.log", r"system\.log", r"error_log",
        r"error\.txt", r"debug\.txt", r"info\.txt", r"log\.txt", r"dump\.txt", r"backup\.txt", r"temp\.txt", r"tmp\.txt",
        r"test\.html", r"test\.htm", r"index\.bak", r"index\.old", r"index\.php\.bak", r"index\.php\.old", r"index\.html\.bak",
        r"index\.html\.old", r"default\.bak", r"default\.old", r"default\.php\.bak", r"default\.php\.old", r"default\.html\.bak",
        r"default\.html\.old", r"app_dev\.php", r"app_test\.php", r"admin_dev\.php", r"admin_test\.php", r"config\.bak",
        r"config\.old", r"config\.php\.bak", r"config\.php\.old", r"settings\.bak", r"settings\.old", r"settings\.php\.bak",
        r"settings\.php\.old", r"database\.bak", r"database\.old", r"database\.sql\.bak", r"database\.sql\.old", r"db\.bak",
        r"db\.old", r"db\.sql\.bak", r"db\.sql\.old", r"dump\.sql", r"backup\.sql", r"data\.sql", r"schema\.sql", r"users\.sql",
        r"passwords\.txt", r"userlist\.txt", r"credentials\.txt", r"secrets\.txt", r"keys\.txt", r"tokens\.txt", r"config\.txt",
        r"settings\.txt", r"database\.txt", r"db\.txt", r"dump\.txt", r"backup\.txt", r"data\.txt", r"schema\.txt", r"users\.txt",
        r"web\.xml", r"server\.xml", r"context\.xml", r"application\.xml", r"pom\.xml", r"build\.xml"
    ]
    sensitive_regex = re.compile("|".join(sensitive_patterns), re.I)

    urls = context.get("urls", [])
    if not urls:
        if os.path.isfile(all_urls_file) and os.path.getsize(all_urls_file) > 0:
            with open(all_urls_file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
            if not urls:
                logger.warning("No URLs available in all_urls.txt for sensitive file extraction.")
                with open(sensitive_file, "w", encoding="utf-8") as f:
                    f.write("No URLs available for sensitive file extraction.\n")
                context["sensitive_urls"] = []
                timer_end(start, "Sensitive File Extraction")
                return
        else:
            logger.warning("No URLs available in context or all_urls.txt for sensitive file extraction.")
            with open(sensitive_file, "w", encoding="utf-8") as f:
                f.write("No URLs available for sensitive file extraction.\n")
            context["sensitive_urls"] = []
            timer_end(start, "Sensitive File Extraction")
            return

    sensitive_urls = [url for url in urls if sensitive_regex.search(url)]

    with open(sensitive_file, "w", encoding="utf-8") as f:
        for url in sensitive_urls:
            f.write(f"{url}\n")

    context["sensitive_urls"] = sorted(sensitive_urls)
    print_found("Sensitive Files", len(sensitive_urls))
    timer_end(start, "Sensitive File Extraction")

def step_js_scan(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🛠️ Scanning JavaScript files for secrets and endpoints")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    all_urls_file = os.path.join(domain_dir, "all_urls.txt")
    js_findings_file = os.path.join(domain_dir, "js_findings.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    js_urls = []
    secrets = []
    endpoints = []

    # Enhanced patterns for secrets and endpoints
    secret_patterns = [
        r"api[_-]?key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Generic API keys
        r"token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Generic tokens
        r"password=['\"][^'\"]{8,}[ '\"]",  # Passwords
        r"secret[_-]?key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Secret keys
        r"access[_-]?key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Access keys
        r"aws_access_key_id=['\"][A-Z0-9]{20}[ '\"]",  # AWS access key
        r"aws_secret_access_key=['\"][a-zA-Z0-9/+=]{40}[ '\"]",  # AWS secret key
        r"firebase\.io['\"][^'\"]+['\"]",  # Firebase URLs
        r"client[_-]?id=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Client IDs
        r"client[_-]?secret=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Client secrets
        r"oauth[_-]?access_token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # OAuth tokens
        r"database[_-]?url=['\"][^'\"]+['\"]",  # Database URLs
        r"mongodb://[^'\"]+['\"]", r"mysql://[^'\"]+['\"]", r"postgres://[^'\"]+['\"]",  # DB connections
        r"slack[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Slack tokens
        r"bearer[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Bearer tokens
        r"jwt=['\"][a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+['\"]",  # JWTs
        r"x-api-key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # API keys
        r"shopify[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Shopify tokens
        r"stripe[_-]?key=['\"][sk|pk]_[a-zA-Z0-9-_]{20,}[ '\"]",  # Stripe keys
        r"github[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # GitHub tokens
        r"gcp[_-]?key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # GCP keys
        r"cloudinary[_-]?url=['\"][^'\"]+['\"]",  # Cloudinary URLs
        r"webhook[_-]?url=['\"][^'\"]+['\"]",  # Webhook URLs
        r"zoom[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Zoom tokens
        r"heroku[_-]?key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Heroku keys
        r"netlify[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Netlify tokens
        r"digitalocean[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # DigitalOcean tokens
        r"bitbucket[_-]?key=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Bitbucket keys
        r"twilio[_-]?auth[_-]?token=['\"][a-zA-Z0-9-_]{20,}[ '\"]",  # Twilio tokens
    ]
    endpoint_patterns = [
        r"['\"]/api/[^'\"]+['\"]",  # API endpoints
        r"['\"]/v[0-9]+/[^'\"]+['\"]",  # Versioned API endpoints
        r"['\"]/graphql['\"]",  # GraphQL endpoints
        r"['\"]/rest/[^'\"]+['\"]",  # REST endpoints
        r"['\"]/ajax/[^'\"]+['\"]",  # AJAX endpoints
        r"['\"]/endpoint/[^'\"]+['\"]",  # Generic endpoints
        r"['\"]/admin/[^'\"]+['\"]",  # Admin endpoints
        r"['\"]/auth/[^'\"]+['\"]",  # Auth endpoints
        r"['\"]/api/v[0-9]+/[^'\"]+['\"]",  # Versioned API endpoints
    ]
    secret_regex = re.compile("|".join(secret_patterns), re.I)
    endpoint_regex = re.compile("|".join(endpoint_patterns), re.I)
    false_positive = re.compile(r"csrf_token|xsrf_token|nonce|form_token", re.I)

    try:
        # Load URLs from all_urls.txt or context
        urls = context.get("urls", [])
        if not urls and os.path.isfile(all_urls_file) and os.path.getsize(all_urls_file) > 0:
            with open(all_urls_file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
        if not urls:
            logger.warning("No URLs available for JS scanning.")
            with open(js_findings_file, "w", encoding="utf-8") as f:
                f.write("No URLs available for JS scanning.\n")
            context["js_findings"] = {"secrets": [], "endpoints": []}
            context.setdefault("failures", []).append(("JS Scan", "No input URLs"))
            timer_end(start, "JavaScript Scanning")
            return

        # Filter for .js URLs
        js_pattern = re.compile(r"\.js$", re.I)
        js_urls = [url for url in urls if js_pattern.search(url)]
        if not js_urls:
            logger.warning("No .js URLs found for scanning.")
            with open(js_findings_file, "w", encoding="utf-8") as f:
                f.write("No .js URLs found for scanning.\n")
            context["js_findings"] = {"secrets": [], "endpoints": []}
            context.setdefault("failures", []).append(("JS Scan", "No JS URLs"))
            timer_end(start, "JavaScript Scanning")
            return

        # Optionally use getJS for dynamic JS extraction
        if shutil.which("getJS"):
            print_step("Running getJS for dynamic JS extraction...")
            temp_getjs_input = os.path.join(domain_dir, "temp_getjs_input.txt")
            temp_getjs_output = os.path.join(domain_dir, "temp_getjs_output.txt")
            with open(temp_getjs_input, "w", encoding="utf-8") as f:
                f.write(f"https://{domain}\n")
            cmd = ["getJS", "--url", f"https://{domain}", "--output", temp_getjs_output]
            result = run_command(cmd, timeout=600, error_log=error_log, capture_output=True)
            if result and os.path.isfile(temp_getjs_output):
                with open(temp_getjs_output, "r", encoding="utf-8") as f:
                    js_urls.extend(line.strip() for line in f if line.strip() and js_pattern.search(line))
                os.remove(temp_getjs_output)
            os.remove(temp_getjs_input)

        # Probe JS URLs with httprobe to ensure they're live
        live_js_urls = []
        if js_urls and shutil.which("httprobe"):
            temp_js_input = os.path.join(domain_dir, "temp_js_probe_input.txt")
            with open(temp_js_input, "w", encoding="utf-8") as f:
                f.write("\n".join(js_urls))
            probe_cmd = ["httprobe", "-c", str(config.get("threads", 100)), "-t", "15000", "-p", "http:80,https:443"]
            probe = subprocess.Popen(
                probe_cmd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore"
            )
            with open(temp_js_input, "r", encoding="utf-8") as f_in:
                out, err = probe.communicate(input=f_in.read(), timeout=300)
            if out:
                live_js_urls = [line.strip() for line in out.splitlines() if line.strip()]
            if os.path.exists(temp_js_input):
                os.remove(temp_js_input)

        if not live_js_urls:
            logger.warning("No live .js URLs found after probing.")
            with open(js_findings_file, "w", encoding="utf-8") as f:
                f.write("No live .js URLs found after probing.\n")
            context["js_findings"] = {"secrets": [], "endpoints": []}
            context.setdefault("failures", []).append(("JS Scan", "No live JS URLs"))
            timer_end(start, "JavaScript Scanning")
            return

        # Scan JS files with curl and regex
        for url in live_js_urls[:50]:  # Limit to 50 to avoid rate-limiting
            random_delay(config.get("intensity", "medium"))
            cmd = ["curl", "-s", "-A", get_random_user_agent(), "-m", "10", url]
            proxy = get_proxy()
            if proxy:
                cmd.extend(["-x", proxy.get("http", "")])
            content = run_command(cmd, timeout=15, error_log=error_log, capture_output=True)
            if content:
                for match in secret_regex.finditer(content):
                    secret = match.group(0)
                    if not false_positive.search(secret):
                        secrets.append(f"{url}: {secret}")
                for match in endpoint_regex.finditer(content):
                    endpoint = match.group(0).strip("'\"")
                    endpoints.append(f"{url}: {endpoint}")

        # Optionally use trufflehog for advanced secret scanning
        if shutil.which("trufflehog"):
            print_step("Running trufflehog for advanced secret scanning...")
            temp_js_urls = os.path.join(domain_dir, "temp_js_urls.txt")
            with open(temp_js_urls, "w", encoding="utf-8") as f:
                f.write("\n".join(live_js_urls))
            cmd = ["trufflehog", "filesystem", temp_js_urls, "--json"]
            result = run_command(cmd, timeout=600, error_log=error_log, capture_output=True)
            if result:
                for line in result.splitlines():
                    try:
                        data = json.loads(line.strip())
                        if data.get("SourceMetadata", {}).get("Data", {}).get("Filesystem"):
                            secret = data.get("Raw")
                            source = data.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("file")
                            secrets.append(f"{source}: {secret}")
                    except json.JSONDecodeError:
                        logger.warning(f"trufflehog output not JSON: {line.strip()}")
            if os.path.exists(temp_js_urls):
                os.remove(temp_js_urls)

        # Save findings
        with open(js_findings_file, "w", encoding="utf-8") as f:
            f.write("=== JavaScript Secrets ===\n")
            for secret in sorted(secrets):
                f.write(f"{secret}\n")
            f.write("\n=== JavaScript Endpoints ===\n")
            for endpoint in sorted(endpoints):
                f.write(f"{endpoint}\n")

        context["js_findings"] = {"secrets": sorted(secrets), "endpoints": sorted(endpoints)}
        print_found("JS Secrets", len(secrets))
        print_found("JS Endpoints", len(endpoints))
        if secrets or endpoints:
            alert("JS Findings", secrets[:5] + endpoints[:5])
        else:
            logger.warning("No secrets or endpoints found in JS files.")
            with open(js_findings_file, "a", encoding="utf-8") as f:
                f.write("No secrets or endpoints found.\n")
            context.setdefault("failures", []).append(("JS Scan", "No findings"))

    except Exception as e:
        alert_error(f"JS scanning failed: {e}", error_log)
        context.setdefault("failures", []).append(("JS Scan", str(e)))

    timer_end(start, "JavaScript Scanning")

def step_dig_dns(domain, config, context):
    if context.get("skip", False):
        return
    print_step("🔎 Gathering DNS records")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    dns_out = os.path.join(domain_dir, "dns_records.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    records = []
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA"]

    if not shutil.which("dig"):
        alert("Dig", ["Binary not found in PATH. Skipping DNS enumeration."])
        context.setdefault("failures", []).append(("Dig", "Binary missing"))
        return

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
                except subprocess.TimeoutExpired:
                    msg = f"[dig] Timeout for {rtype} record on {domain}"
                    logger.warning(msg)
                    alert_error(msg, error_log)
                    context.setdefault("failures", []).append((f"Dig {rtype}", "Timeout"))
                except Exception as e:
                    msg = f"[dig] Failed for {rtype}: {e}"
                    logger.warning(msg)
                    alert_error(msg, error_log)
                    context.setdefault("failures", []).append((f"Dig {rtype}", str(e)))

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
            context.setdefault("failures", []).append(("DNS", "No records found"))

    except Exception as e:
        alert_error(f"[dig] DNS enumeration failed: {e}", error_log)
        context.setdefault("failures", []).append(("Dig", str(e)))

    timer_end(start, "DNS Enumeration")

def step_naabu_ports(domain, config, context):
    if context.get("skip", False):
        return
    if not config.get("run_naabu", False):
        print_step("⏭️ Naabu disabled in config")
        return

    print_step("🚪 Scanning open ports with Naabu")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)

    naabu_out = os.path.join(domain_dir, "naabu_ports.txt")
    error_log = os.path.join(domain_dir, "errors.log")
    ports = set()
    targets = context.get("live_subdomains", []) or [domain]
    ip_targets = set()

    if not shutil.which("naabu"):
        alert("Naabu", ["Binary not found in PATH. Skipping port scan."])
        context.setdefault("failures", []).append(("Naabu", "Binary missing"))
        return

    for target in targets:
        try:
            result = run_command(
                ["dig", "+short", target, "A"],
                timeout=15,
                error_log=error_log,
                capture_output=True
            )
            if result:
                ips = [line.strip() for line in result.splitlines() if re.match(r"^\d+\.\d+\.\d+\.\d+$", line.strip())]
                ip_targets.update(ips)
        except Exception as e:
            logger.warning(f"Failed to resolve IP for {target}: {e}")

    targets = list(set(targets) | ip_targets)

    if not targets:
        alert("Naabu", ["No targets (live subdomains or IPs) to scan."])
        context.setdefault("failures", []).append(("Naabu", "No targets"))
        return

    for target in targets:
        port_range = "1-1000"
        cmd = ["naabu", "-host", target, "-p", port_range, "-silent", "-rate", "1500", "-json"]

        try:
            result = run_command(cmd, timeout=5000, error_log=error_log, capture_output=True)
            if result:
                for line in result.splitlines():
                    try:
                        data = json.loads(line.strip())
                        if "host" in data and "port" in data:
                            ports.add(f"{data['host']}:{data['port']}")
                    except json.JSONDecodeError:
                        logger.warning(f"Naabu output line not JSON: {line.strip()}")
                        match = re.match(r"([\d.]+):(\d+)", line.strip())
                        if match:
                            ports.add(f"{match.group(1)}:{match.group(2)}")
        except subprocess.TimeoutExpired:
            logger.warning(f"[Naabu] Timeout on {target}, falling back to top-ports")
            alert("Naabu Timeout", [f"{target} took too long, using fallback"])
            cmd = ["naabu", "-host", target, "-top-ports", "1000", "-silent", "-rate", "2000", "-json"]
            try:
                result = run_command(cmd, timeout=780, error_log=error_log, capture_output=True)
                if result:
                    for line in result.splitlines():
                        try:
                            data = json.loads(line.strip())
                            if "host" in data and "port" in data:
                                ports.add(f"{data['host']}:{data['port']}")
                        except json.JSONDecodeError:
                            logger.warning(f"Naabu output line not JSON (fallback): {line.strip()}")
                            match = re.match(r"([\d.]+):(\d+)", line.strip())
                            if match:
                                ports.add(f"{match.group(1)}:{match.group(2)}")
            except Exception as e:
                alert_error(f"Naabu fallback failed on {target}: {e}", error_log)
                context.setdefault("failures", []).append((f"Naabu fallback: {target}", str(e)))
                continue
        except Exception as e:
            alert_error(f"Naabu failed on {target}: {e}", error_log)
            context.setdefault("failures", []).append((f"Naabu error: {target}", str(e)))
            continue

    context["open_ports"] = sorted(ports)

    with open(naabu_out, "w", encoding="utf-8") as f:
        for port_entry in sorted(ports):
            f.write(f"{port_entry}\n")

    if ports:
        print_found("Open Ports", len(ports))
        alert("Open Ports", sorted(ports))
    else:
        logger.info("No open ports detected by Naabu.")
        alert("Naabu", ["No open ports found"])
        context.setdefault("failures", []).append(("Naabu", "No ports found"))

    timer_end(start, "Port Scanning")

def step_sqlmap(domain, config, context):
    if context.get("skip", False):
        return
    if not config.get("run_sqlmap", False):
        print_step("⏭️ SQLMap disabled in config")
        return

    print_step("🧪 Running SQLMap with advanced techniques")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    error_log = os.path.join(domain_dir, "errors.log")
    live_param_urls_file = os.path.join(domain_dir, "live_param_urls.txt")
    sqlmap_logs = []

    if not shutil.which("sqlmap"):
        alert("SQLMap", ["Binary not found. Skipping SQLMap scan."])
        context.setdefault("failures", []).append(("SQLMap", "Binary missing"))
        return

    if not os.path.isfile(live_param_urls_file) or os.path.getsize(live_param_urls_file) == 0:
        alert("SQLMap", ["No live parameter URLs for scanning"])
        with open(error_log, "a", encoding="utf-8") as f:
            f.write("SQLMap skipped — no live param URLs.\n")
        context.setdefault("failures", []).append(("SQLMap", "No input URLs"))
        return

    try:
        with open(live_param_urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        max_urls = 5 if config.get("intensity") == "light" else 10
        urls_to_scan = urls[:max_urls]
        if len(urls) > max_urls:
            logger.warning(f"SQLMap: Limiting scan to first {max_urls} URLs out of {len(urls)} found.")

        for i, url in enumerate(urls_to_scan):
            sqlmap_dir = os.path.join(domain_dir, f"sqlmap_output_{i+1}")
            os.makedirs(sqlmap_dir, exist_ok=True)
            random_delay(config.get("intensity"))

            cmd = [
                "sqlmap", "-u", url,
                "--batch",
                "--random-agent",
                "--level", "5", "--risk", "3",
                "--dbs", "--banner", "--is-dba", "--current-db", "--current-user",
                "--technique", "BEUSTQ",
                "--tamper", "space2comment,between,randomcase,space2plus,charunicodeencode,modsecurityversioned",
                "--output-dir", sqlmap_dir,
                "--timeout", "60", "--retries", "3", "--delay", "1",
                "--crawl", "3", "--forms", "--parse-errors",
                "--dump-all", "--dump-format", "csv"
            ]

            proxy = get_proxy()
            if proxy:
                cmd.extend(["--proxy", proxy.get("http", "")])

            logger.info(f"Running SQLMap on URL {i+1}: {url}")
            run_command(cmd, timeout=1800, error_log=error_log)
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

    timer_end(start, "SQL injection scan")

def step_dir_fuzz(domain, config, context):
    if context.get("skip", False):
        return
    if not config.get("dir_fuzz_tool", False):
        print_step("⏭️ Directory fuzzing disabled in config")
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
        alert("Fuzzing", ["Wordlist not found or not configured. Skipping directory fuzzing."])
        context.setdefault("failures", []).append(("Fuzz", "Missing wordlist"))
        return

    if fuzz_tool == "ffuf":
        if not shutil.which("ffuf"):
            alert("FFUF", ["Binary not found. Skipping FFUF scan."])
            context.setdefault("failures", []).append(("FFUF", "Binary missing"))
            return
        try:
            temp_file = os.path.join(domain_dir, "ffuf_temp.json")
            cmd = [
                "ffuf", "-u", f"https://{domain}/FUZZ",
                "-w", wordlist,
                "-mc", "200,204,301,302,307,403",
                "-t", str(config.get("threads", 40)),
                "-o", temp_file,
                "-of", "json",
                "-recursion", "-recursion-depth", "2",
                "-v"
            ]
            proxy = get_proxy()
            if proxy:
                cmd.extend(["-x", proxy.get("http", "")])

            run_command(cmd, timeout=8000, error_log=error_log)

            if os.path.isfile(temp_file):
                with open(temp_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for result in data.get("results", []):
                        url = result.get("url")
                        status = result.get("status")
                        length = result.get("length")
                        if url and status in [200, 204, 301, 302, 307, 403]:
                            found_dirs.add(f"[{status}] {url} ({length} bytes)")
                os.remove(temp_file)

        except Exception as e:
            alert_error(f"FFUF fuzz failed: {e}", error_log)
            context.setdefault("failures", []).append(("FFUF", str(e)))
            return

    elif fuzz_tool == "dirsearch":
        if not shutil.which("dirsearch"):
            alert("Dirsearch", ["Binary not found. Skipping Dirsearch scan."])
            context.setdefault("failures", []).append(("Dirsearch", "Binary missing"))
            return
        raw_out = os.path.join(domain_dir, "dirsearch_raw.txt")
        try:
            run_command([
                "dirsearch", "-u", f"https://{domain}",
                "-w", wordlist, "-e", "php,html,aspx,jsp,json,xml,js,txt,log,bak,zip,tar,gz,rar,7z,sql,env,conf,ini,yml,yaml,git,svn,old,bak,temp,tmp,test,debug,error,access,install,setup,update,upgrade,composer,package,yarn,npm,server,application,system,info,dump,backup,data,schema,users,web,context,pom,build,swagger,api-docs,graphql,adminer,phpmyadmin,phpPgAdmin",
                "-t", str(config.get("threads", 20)),
                "--format=plain", f"--output={raw_out}",
                "--full-url",
                "--recursion-status", "200,204,301,302,307,403",
                "--recursion-depth", "2"
            ], timeout=8000, error_log=error_log)

            if os.path.isfile(raw_out):
                with open(raw_out, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("http"):
                            found_dirs.add(line.strip())
                os.remove(raw_out)

        except Exception as e:
            alert_error(f"Dirsearch failed: {e}", error_log)
            context.setdefault("failures", []).append(("Dirsearch", str(e)))
            return

    else:
        alert("Fuzzing", [f"Unknown fuzz tool: {fuzz_tool}. Please choose 'ffuf' or 'dirsearch'."])
        context.setdefault("failures", []).append(("Fuzz", f"Unknown tool: {fuzz_tool}"))
        return

    with open(fuzz_out, "w", encoding="utf-8") as f:
        for dir_entry in sorted(found_dirs):
            f.write(f"{dir_entry}\n")

    context["dir_fuzz"] = sorted(found_dirs)
    print_found("Fuzzed Directories/Files", len(found_dirs))
    if found_dirs:
        alert("Fuzzed Directories/Files", list(found_dirs)[:10])
    else:
        alert("Fuzzing", ["No directories or files found."])

    timer_end(start, "Directory Fuzzing")

def step_generate_report(domain, config, context):
    if context.get("skip", False):
        return
    print_step("📝 Generating report")
    start = timer_start()
    outdir = config.get("output_dir", "output")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    report_file = os.path.join(domain_dir, "report.html")
    error_log = os.path.join(domain_dir, "errors.log")

    try:
        generate_report(domain, context, report_file)
        print_step(f"Report generated at {report_file}")
    except Exception as e:
        alert_error(f"Report generation failed: {e}", error_log)
        context.setdefault("failures", []).append(("Report Generation", str(e)))

    timer_end(start, "Report Generation")

def get_steps_for_intensity(intensity):
    base_steps = [
        step_check_dependencies,
        step_subdomain_enum,
        step_wayback_urls,
        step_waymore_urls,
        step_assetfinder_crawl,
        step_param_discovery,
        step_parse_param_urls,
        step_probe_param_urls,
        step_extract_juicy_info,
        step_extract_sensitive_files,
        step_js_scan
    ]
    
    if intensity == "light":
        return base_steps
    
    medium_steps = base_steps + [
        step_js_scan,
        step_subjack_takeover,
        step_dig_dns
    ]
    
    if intensity == "medium":
        return medium_steps
    
    deep_steps = medium_steps + [
        step_sqlmap,
        step_dir_fuzz,
        step_naabu_ports
    ]
    
    return deep_steps if intensity == "deep" else medium_steps
