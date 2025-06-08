import os
import subprocess
import re
import hashlib
import time

def timer_start():
    return time.time()

def timer_end(start_time, step_name="Step"):
    duration = int(time.time() - start_time)
    print(f"\033[1;34m[*] {step_name} completed in {duration}s\033[0m")

def extract_sensitive_files(domain, outdir):
    print(f"\033[1;36m[+] Extracting sensitive files and links for {domain}\033[0m")
    start = timer_start()
    wayback_file = f"{outdir}/{domain}/waybackurls.txt"
    sensitive_file = f"{outdir}/{domain}/sensitive_files.txt"
    error_log = f"{outdir}/{domain}/errors.log"

    sensitive_patterns = [
        r"\.env$", r"\.bak$", r"\.sql$", r"\.config$", r"\.conf$", r"\.json$",
        r"\.yaml$", r"\.yml$", r"\.log$", r"\.backup$", r"\.git/", r"\.svn/",
        r"phpinfo\.php$", r"admin", r"login", r"dashboard", r"wp-admin",
        r"wp-login\.php", r"config\.php", r"settings", r"backup"
    ]
    sensitive_regex = "|".join(sensitive_patterns)

    if os.path.isfile(wayback_file):
        try:
            with open(wayback_file) as fin, open(sensitive_file, "w") as fout:
                found = False
                for line in fin:
                    if re.search(sensitive_regex, line):
                        fout.write(line)
                        found = True
                if found:
                    fout.write(f"\n# Sensitive Files and Links for {domain}\n")
                else:
                    fout.write("No sensitive files or links found.\n")
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"Failed to grep sensitive files: {e}\n")
    timer_end(start, "Sensitive file extraction")

def grep_juicy_info(domain, outdir):
    print(f"\033[1;36m[+] Grepping juicy info from waybackurls and JS files for {domain}\033[0m")
    start = timer_start()
    wayback_file = f"{outdir}/{domain}/waybackurls.txt"
    juicy_file = f"{outdir}/{domain}/juicy_info.txt"
    js_dir = f"{outdir}/{domain}/js_files"
    error_log = f"{outdir}/{domain}/errors.log"
    os.makedirs(js_dir, exist_ok=True)

    patterns = [
        r"api[_-]?key", r"token", r"password", r"secret", r"access[_-]?key", r"aws[_-]?key",
        r"aws[_-]?secret", r"auth[_-]?token", r"session[_-]?id", r"credential", r"stripe[_-]?key",
        r"s3\.amazonaws\.com", r"blob\.core\.windows\.net", r"firebaseio\.com", r"client[_-]?id",
        r"client[_-]?secret", r"oauth", r"db[_-]?password", r"database[_-]?url", r"[0-9a-f]{32,}",
        r"key=[a-zA-Z0-9_-]+", r"jwt=[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
        r"mongodb\+srv://", r"mysql://", r"postgres://", r"slack[_-]?token", r"bearer[_-]?token"
    ]
    pattern_regex = "|".join(patterns)

    if os.path.isfile(wayback_file):
        try:
            with open(wayback_file) as fin, open(juicy_file, "w") as fout:
                found = False
                for line in fin:
                    if re.search(pattern_regex, line, re.I):
                        fout.write(line)
                        found = True
                # Extract live JS URLs with httprobe (simulate with curl for Python version)
                js_urls = []
                fin.seek(0)
                for line in fin:
                    if line.lower().strip().endswith(".js"):
                        js_urls.append(line.strip())
                for url in js_urls:
                    # Use SHA1 hash of URL as filename
                    filename = hashlib.sha1(url.encode()).hexdigest() + ".js"
                    js_path = os.path.join(js_dir, filename)
                    try:
                        subprocess.run(["curl", "-s", "-m", "10", url, "-o", js_path], check=True)
                        if os.path.isfile(js_path):
                            with open(js_path) as jsf:
                                for jsline in jsf:
                                    if re.search(pattern_regex, jsline, re.I):
                                        fout.write(f"[JS] {url}: {jsline}")
                                        found = True
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

def scan_domain(
    domain, outdir, threads, hak_depth, sqlmap_flags, wordlist, selected_tools, recursion_depth, subdomain_scan
):
    print(f"\n\033[1;33m[*] Starting scan for {domain}\033[0m")
    domain_dir = os.path.join(outdir, domain)
    os.makedirs(domain_dir, exist_ok=True)
    error_log = os.path.join(domain_dir, "errors.log")

    # timer_start is called at each step, timer_end(step_name) at the end
    steps = [
        ("theHarvester", lambda: subprocess.run([
            "theHarvester", "-d", domain, "-b", "all", "-f", f"{domain_dir}/harvest.html"
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))),

        ("subjack", lambda: subprocess.run([
            "subjack", "-w", domain, "-t", str(threads), "-timeout", "30",
            "-o", f"{domain_dir}/subjack.txt", "-ssl"
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))),

        ("waybackurls", lambda: subprocess.run([
            "waybackurls"
        ], input=f"{domain}\n".encode(), stdout=open(f"{domain_dir}/waybackurls.txt", "w"),
           stderr=open(error_log, "a"))),

        ("extract_sensitive_files", lambda: extract_sensitive_files(domain, outdir)),
        ("grep_juicy_info", lambda: grep_juicy_info(domain, outdir)),

        ("nuclei", lambda: subprocess.run([
            "nuclei", "-u", domain, "-o", f"{domain_dir}/nuclei.txt"
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))),

        ("ffuf", lambda: subprocess.run([
            "ffuf", "-w", wordlist, "-u", f"https://{domain}/FUZZ", "-t", str(threads),
            "-s", "-mc", "200,301,302", "-ac", "-o", f"{domain_dir}/ffuf.json", "-of", "json"
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))),

        ("dalfox", lambda: subprocess.run([
            "dalfox", "url", domain, "--output", f"{domain_dir}/dalfox.txt"
        ], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))),

        ("sqlmap", lambda: subprocess.run([
            "sqlmap", "-u", f"https://{domain}"] + sqlmap_flags.split() +
            ["--batch", f"--output-dir={domain_dir}/sqlmap"],
            stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))),
    ]

    for step_name, step_func in steps:
        print(f"\033[1;36m[+] Running {step_name} for {domain}\033[0m")
        start = timer_start()
        try:
            step_func()
        except Exception as e:
            with open(error_log, "a") as ferr:
                ferr.write(f"{step_name} failed: {str(e)}\n")
        timer_end(start, step_name)

    # Generate summary
    summary_path = f"{domain_dir}/summary.md"
    with open(summary_path, "w") as fsum:
        fsum.write(f"# Summary for {domain}\n")
        for fname in os.listdir(domain_dir):
            fpath = os.path.join(domain_dir, fname)
            if os.path.isfile(fpath) and fname != "summary.md":
                fsum.write(f"\n## {fname}\n\n```text\n")
                with open(fpath, "r", errors="ignore") as fin:
                    for i, line in enumerate(fin):
                        if i == 30:
                            fsum.write("...\n")
                            break
                        fsum.write(line)
                fsum.write("```\n")
    # Export to PDF (optional, requires pandoc)
    try:
        subprocess.run(["pandoc", summary_path, "-o", f"{domain_dir}/summary.pdf"], stdout=subprocess.DEVNULL, stderr=open(error_log, "a"))
    except Exception as e:
        with open(error_log, "a") as ferr:
            ferr.write(f"pandoc failed: {str(e)}\n")
