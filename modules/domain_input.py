import re

def validate_domain(domain):
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$", domain))

def load_domains(domains_file, outdir):
    error_log = f"{outdir}/error.log"
    try:
        with open(domains_file, "r") as f:
            all_domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        print(f"\033[1;31m[!] File '{domains_file}' not found or not readable.\033[0m")
        with open(error_log, "a") as f:
            f.write(f"File '{domains_file}' not found or not readable.\n")
        exit(1)
    cleaned_domains = []
    for dom in all_domains:
        cleaned = re.sub(r"^https?://", "", dom)
        cleaned = re.sub(r"/.*", "", cleaned)
        cleaned = re.sub(r"^\*\.", "", cleaned)
        if validate_domain(cleaned):
            cleaned_domains.append(cleaned)
        else:
            with open(error_log, "a") as f:
                f.write(f"Invalid domain skipped: {dom}\n")
    if not cleaned_domains:
        print("\033[1;31m[!] No valid domains found in file.\033[0m")
        with open(error_log, "a") as f:
            f.write("No valid domains found in file.\n")
        exit(1)
    return cleaned_domains

def get_domains(outdir):
    error_log = f"{outdir}/error.log"
    selected_domains = []
    while True:
        print("\033[1;36m[?] Select how to provide domains:\033[0m")
        print("\033[1;33m  1) Enter domains manually\033[0m")
        print("\033[1;33m  2) Load domains from a file\033[0m")
        try:
            input_method = input("> ").strip()
        except Exception:
            print("\033[1;31m[!] Input timed out.\033[0m")
            exit(1)
        if input_method == "1":
            input_domains = input("Enter 1-10 domains (space-separated): ").strip()
            if not input_domains:
                print("\033[1;31m[!] No domains entered.\033[0m")
                continue
            domains = input_domains.split()
            if len(domains) > 10:
                print("\033[1;31m[!] Too many domains. Enter 1-10.\033[0m")
                continue
            valid_domains = [d for d in domains if validate_domain(d)]
            if not valid_domains:
                print("\033[1;31m[!] No valid domains provided.\033[0m")
                continue
            selected_domains = valid_domains
            break
        elif input_method == "2":
            domains_file = input("Enter the full path to the domains file: ").strip()
            cleaned_domains = load_domains(domains_file, outdir)
            try:
                domain_count = int(input("How many domains to scan (1-10)? ").strip())
            except Exception:
                print("\033[1;31m[!] Invalid input.\033[0m")
                continue
            if not (1 <= domain_count <= 10):
                print("\033[1;31m[!] Invalid number. Enter 1 to 10.\033[0m")
                continue
            try:
                import shutil
                if shutil.which("fzf"):
                    print("[*] Interactive selection (fzf) not implemented in this sample for cross-platform support.")
                    selected_domains = cleaned_domains[:domain_count]
                else:
                    print("\033[1;31m[!] fzf not installed. Selecting first domains.\033[0m")
                    selected_domains = cleaned_domains[:domain_count]
            except Exception:
                selected_domains = cleaned_domains[:domain_count]
            break
        else:
            print("\033[1;31m[!] Invalid choice. Enter '1' or '2'.\033[0m")
    return selected_domains
