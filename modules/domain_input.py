import re
import os
import logging
import sys

MAX_DOMAINS = 100
ERROR_LOG = "error.log"

# Only use color in interactive terminals
def supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

CYAN = "\033[1;36m" if supports_color() else ""
GREEN = "\033[1;32m" if supports_color() else ""
YELLOW = "\033[1;33m" if supports_color() else ""
RED = "\033[1;31m" if supports_color() else ""
RESET = "\033[0m" if supports_color() else ""

def validate_domain(domain):
    """Validate a domain name using regex."""
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$", domain))

def clean_domain(dom):
    """Strip protocol, path, and wildcards from a domain string."""
    cleaned = re.sub(r"^https?://", "", dom)
    cleaned = re.sub(r"/.*", "", cleaned)
    cleaned = re.sub(r"^\*\.", "", cleaned)
    return cleaned

def log_error(message, outdir):
    """Log an error message to the output directory."""
    err_path = os.path.join(outdir, ERROR_LOG)
    with open(err_path, "a") as f:
        f.write(message + "\n")
    logging.error(message)

def load_domains(domains_file, outdir):
    """Load and sanitize domains from a file."""
    try:
        with open(domains_file, "r") as f:
            all_domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        log_error(f"File '{domains_file}' not found or not readable.", outdir)
        print(f"{RED}[!] File '{domains_file}' not found or not readable.{RESET}", file=sys.stderr)
        raise FileNotFoundError(f"File '{domains_file}' not found or not readable.")
    cleaned_domains = []
    for dom in all_domains:
        cleaned = clean_domain(dom)
        if validate_domain(cleaned):
            cleaned_domains.append(cleaned)
        else:
            log_error(f"Invalid domain skipped: {dom}", outdir)
            print(f"{YELLOW}[!] Invalid domain skipped: {dom}{RESET}", file=sys.stderr)
    if not cleaned_domains:
        log_error("No valid domains found in file.", outdir)
        print(f"{RED}[!] No valid domains found in file.{RESET}", file=sys.stderr)
        raise ValueError("No valid domains found in file.")
    return cleaned_domains

def get_domains_interactive(outdir):
    """Interactive, colorized, hacker-style domain input. No banners or mixing, pure logic."""
    print(f"{CYAN}[?] How do you want to input domains?{RESET}")
    print(f"{GREEN}  1){RESET} Manually (type/paste domains)")
    print(f"{CYAN}  2){RESET} Load from file")
    while True:
        choice = input(f"{YELLOW}Select option [1/2]:{RESET} ").strip()
        if choice == "1":
            print(f"{CYAN}[+] Enter 1-{MAX_DOMAINS} domains (comma or space separated):{RESET}")
            while True:
                raw = input(f"{GREEN}Domains:{RESET} ").strip()
                if not raw:
                    print(f"{RED}[!] No domains entered. Try again.{RESET}")
                    continue
                domains = [clean_domain(d) for d in raw.replace(',', ' ').split() if d.strip()]
                if len(domains) > MAX_DOMAINS:
                    print(f"{RED}[!] Too many domains. Enter 1-{MAX_DOMAINS}.{RESET}")
                    continue
                valid_domains = [d for d in domains if validate_domain(d)]
                if not valid_domains:
                    print(f"{RED}[!] No valid domains provided. Try again.{RESET}")
                    continue
                print(f"{GREEN}[+] Domains accepted:{RESET} {CYAN}{', '.join(valid_domains)}{RESET}")
                return valid_domains
        elif choice == "2":
            print(f"{CYAN}[+] Enter path to domain file:{RESET}")
            while True:
                path = input(f"{GREEN}File path:{RESET} ").strip()
                if not os.path.isfile(path):
                    print(f"{RED}[!] File not found. Try again.{RESET}")
                    continue
                try:
                    domains = load_domains(path, outdir)
                    print(f"{GREEN}[+] Domains loaded:{RESET} {CYAN}{', '.join(domains)}{RESET}")
                    return domains
                except Exception as e:
                    print(f"{RED}[!] {e}{RESET}")
        else:
            print(f"{RED}[!] Invalid input. Choose 1 or 2.{RESET}")

def get_domains(outdir):
    """Check env for domains, else go interactive."""
    env_domains = os.environ.get("VENO_DOMAINS")
    if env_domains:
        domains = [clean_domain(d) for d in env_domains.replace(',', ' ').split() if d.strip()]
        valid_domains = [d for d in domains if validate_domain(d)]
        if not valid_domains:
            log_error("[VENO] No valid domains provided via VENO_DOMAINS env.", outdir)
            print(f"{RED}[!] No valid domains from VENO_DOMAINS env.{RESET}", file=sys.stderr)
            raise ValueError("No valid domains from VENO_DOMAINS env.")
        print(f"{GREEN}[+] Domains from environment:{RESET} {CYAN}{', '.join(valid_domains)}{RESET}")
        return valid_domains
    # Interactive fallback
    return get_domains_interactive(outdir)
