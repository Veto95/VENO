import re
import os
import logging

MAX_DOMAINS = 100  # Let the user go wild
ERROR_LOG = "error.log"

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
    """Use CLI input or environment variable for domains (headless mode)."""
    env_domains = os.environ.get("VENO_DOMAINS")
    if env_domains:
        domains = [clean_domain(d) for d in env_domains.replace(',', ' ').split() if d.strip()]
        valid_domains = [d for d in domains if validate_domain(d)]
        if not valid_domains:
            log_error("[VENO] No valid domains provided via VENO_DOMAINS env.", outdir)
            raise ValueError("No valid domains from VENO_DOMAINS env.")
        return valid_domains
    # Fallback: prompt user (for interactive fallback only)
    input_domains = input(f"Enter 1-{MAX_DOMAINS} domains (space/comma separated): ").strip()
    if not input_domains:
        log_error("[VENO] No domains entered.", outdir)
        raise ValueError("No domains entered.")
    domains = [clean_domain(d) for d in input_domains.replace(',', ' ').split() if d.strip()]
    if len(domains) > MAX_DOMAINS:
        log_error(f"[VENO] Too many domains. Enter 1-{MAX_DOMAINS}.", outdir)
        raise ValueError("Too many domains.")
    valid_domains = [d for d in domains if validate_domain(d)]
    if not valid_domains:
        log_error("[VENO] No valid domains provided.", outdir)
        raise ValueError("No valid domains provided.")
    return valid_domains
