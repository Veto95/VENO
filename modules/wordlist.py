import os
import logging

COMMON_WORDLISTS = {
    "SecLists: Discovery/Web-Content/common.txt": "/usr/share/seclists/Discovery/Web-Content/common.txt",
    "SecLists: Discovery/Web-Content/big.txt": "/usr/share/seclists/Discovery/Web-Content/big.txt",
    "Dirbuster: directory-list-2.3-small.txt": "/usr/share/dirbuster/wordlists/directory-list-2.3-small.txt"
}

def get_wordlist(output_dir):
    # Check environment variable for automation/headless mode
    env_wordlist = os.environ.get("VENO_WORDLIST")
    if env_wordlist and os.path.isfile(env_wordlist):
        logging.info(f"Using wordlist from VENO_WORDLIST: {env_wordlist}")
        return env_wordlist

    # List common wordlists for interactive selection
    print("\n[VENO] Wordlist Selection")
    print("Available wordlists:")
    for idx, (desc, path) in enumerate(COMMON_WORDLISTS.items(), 1):
        print(f"  {idx}: {desc} ({path})")
    print("  0: Enter custom path")
    while True:
        try:
            choice = int(input("Select wordlist [0/1/2/3]: "))
            if choice == 0:
                path = input("Enter full path to your wordlist: ").strip()
                if os.path.isfile(path):
                    return path
                else:
                    print("[!] File not found. Try again.")
            elif 1 <= choice <= len(COMMON_WORDLISTS):
                path = list(COMMON_WORDLISTS.values())[choice - 1]
                if os.path.isfile(path):
                    return path
                else:
                    print(f"[!] Wordlist not found: {path}")
            else:
                print("[!] Invalid choice.")
        except ValueError:
            print("[!] Please enter a number.")
