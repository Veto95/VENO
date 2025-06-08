import os

ERROR_LOG = "error.log"

def log_error(message, outdir):
    """Log an error message to the output directory."""
    err_path = os.path.join(outdir, ERROR_LOG)
    with open(err_path, "a") as f:
        f.write(message + "\n")

def get_subdomain_scan_choice(outdir, default=None):
    """
    Prompt the user to enable or disable subdomain enumeration.
    Accepts a default (True/False) for automation/testing.
    Returns:
        bool: True if subdomain scanning is enabled, False otherwise.
    """
    print("\n\033[1;36m[VENO] SUBDOMAIN ENUMERATION\033[0m")
    print("Would you like to include subdomain enumeration in your scan?")
    print("This process may increase the scan time but can reveal additional attack surface.")
    while True:
        try:
            if default is not None:
                scan = "yes" if default else "no"
                print(f"Enable subdomain scan? (yes/no): {scan}")
            else:
                scan = input("Enable subdomain scan? (yes/no): ").strip().lower()
        except Exception:
            log_error("Input error for subdomain scan choice.", outdir)
            raise RuntimeError("Input error for subdomain scan choice.")
        if scan in ["yes", "y"]:
            print("\033[1;32m[+] Subdomain enumeration enabled.\033[0m")
            return True
        elif scan in ["no", "n"]:
            print("\033[1;33m[-] Subdomain enumeration disabled.\033[0m")
            return False
        else:
            print("\033[1;31m[!] Please enter 'yes' or 'no'.\033[0m")
            log_error(f"Invalid input for subdomain scan choice: {scan}", outdir)
