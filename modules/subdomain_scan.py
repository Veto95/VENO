def get_subdomain_scan_choice(outdir):
    """
    Prompt the user to enable or disable subdomain enumeration.
    Returns:
        bool: True if subdomain scanning is enabled, False otherwise.
    """
    print("\n\033[1;36m[VENO] SUBDOMAIN ENUMERATION\033[0m")
    print("Would you like to include subdomain enumeration in your scan?")
    print("This process may increase the scan time but can reveal additional attack surface.")
    while True:
        scan = input("Enable subdomain scan? (yes/no): ").strip().lower()
        if scan in ["yes", "y"]:
            print("\033[1;32m[+] Subdomain enumeration enabled.\033[0m")
            return True
        elif scan in ["no", "n"]:
            print("\033[1;33m[-] Subdomain enumeration disabled.\033[0m")
            return False
        else:
            print("\033[1;31m[!] Please enter 'yes' or 'no'.\033[0m")
