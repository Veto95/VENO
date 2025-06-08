import re
import os

MAX_DOMAINS = 20  # Unleash more domains per scan!
ERROR_LOG = "error.log"

def validate_domain(domain):
    """Validate a domain name using regex."""
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$", domain))

def log_error(message, outdir):
    """Log an error message to the output directory."""
    err_path = os.path.join(outdir, ERROR_LOG)
    with open(err_path, "a") as f:
        f.write(message + "\n")

def clean_domain(dom):
    """Strip protocol, path, and wildcards from a domain string."""
    cleaned = re.sub(r"^https?://", "", dom)
    cleaned = re.sub(r"/.*", "", cleaned)
    cleaned = re.sub(r"^\*\.", "", cleaned)
    return cleaned

def load_domains(domains_file, outdir):
    """Load and sanitize domains from a file."""
    try:
        with open(domains_file, "r") as f:
            all_domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        log_error(f"File '{domains_file}' not found or not readable.", outdir)
        raise FileNotFoundError(f"File '{domains_file}' not found or not readable.")
    cleaned_domains = []
    for dom in all_domains:
        cleaned = clean_domain(dom)
        if validate_domain(cleaned):
            cleaned_domains.append(cleaned)
        else:
            log_error(f"Invalid domain skipped: {dom}", outdir)
    if not cleaned_domains:
        log_error("No valid domains found in file.", outdir)
        raise ValueError("No valid domains found in file.")
    return cleaned_domains

def get_domains(outdir):
    """Prompt user to select domains: manual or file input, with optional fzf support."""
    import shutil
    selected_domains = []
    while True:
        print("\033[1;36m[?] Select how to provide domains:\033[0m")
        print("\033[1;33m  1) Enter domains manually\033[0m")
        print(f"\033[1;33m  2) Load domains from a file\033[0m")
        try:
            input_method = input("> ").strip()
        except Exception:
            log_error("Input timed out.", outdir)
            raise RuntimeError("Input timed out.")
        if input_method == "1":
            input_domains = input(f"Enter 1-{MAX_DOMAINS} domains (space-separated): ").strip()
            if not input_domains:
                print("\033[1;31m[!] No domains entered.\033[0m")
                continue
            domains = input_domains.split()
            if len(domains) > MAX_DOMAINS:
                print(f"\033[1;31m[!] Too many domains. Enter 1-{MAX_DOMAINS}.\033[0m")
                continue
            valid_domains = [d for d in domains if validate_domain(d)]
            if not valid_domains:
                print("\033[1;31m[!] No valid domains provided.\033[0m")
                continue
            selected_domains = valid_domains
            break
        elif input_method == "2":
            domains_file = input("Enter the full path

