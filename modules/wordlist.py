import os
import logging

# \GOD MODE/: Common wordlists for pure web/content enumeration
COMMON_WORDLISTS = {
    "SecLists: Discovery/Web-Content/common.txt": "/usr/share/seclists/Discovery/Web-Content/common.txt",
    "SecLists: Discovery/Web-Content/big.txt": "/usr/share/seclists/Discovery/Web-Content/big.txt",
    "Dirbuster: directory-list-2.3-small.txt": "/usr/share/dirbuster/wordlists/directory-list-2.3-small.txt"
}

def color(text, code):
    """Return text wrapped in ANSI color codes."""
    return f"\033[{code}m{text}\033[0m"

def get_wordlist(output_dir=None):
    """
    Prompts the user to select a wordlist for scanning.
    - If VENO_WORDLIST env is set and valid, uses that (automation).
    - Otherwise, presents common wordlists and lets the user choose interactively.
    - Ensures the chosen wordlist exists before returning.
    Returns the path to the wordlist.
    """
    # Automation/headless mode via env
    env_wordlist = os.environ.get("VENO_WORDLIST")
    if env_wordlist and os.path.isfile(env_wordlist):
        msg = f"[VENO] Using wordlist from VENO_WORDLIST: {env_wordlist}"
        logging.info(color(msg, "1;32"))
        print(color(msg, "1;32"))
        return env_wordlist

    # Interactive selection
    print(color("\n[VENO] Wordlist Selection", "1;36"))
    print(color("Available wordlists:", "1;37"))
    for idx, (desc, path) in enumerate(COMMON_WORDLISTS.items(), 1):
        print(color(f"  {idx}: {desc} ({path})", "1;33"))
    print(color("  0: Enter custom path", "1;35"))

    while True:
        try:
            choice = input(color("Select wordlist [0/1/2/3]: ", "1;34"))
            choice = int(choice)
            if choice == 0:
                path = input(color("Enter full path to your wordlist: ", "1;35")).strip()
                if os.path.isfile(path):
                    print(color(f"[VENO] Using custom wordlist: {path}", "1;32"))
                    return path
                else:
                    print(color("[!] File not found. Try again.", "1;31"))
            elif 1 <= choice <= len(COMMON_WORDLISTS):
                path = list(COMMON_WORDLISTS.values())[choice - 1]
                if os.path.isfile(path):
                    print(color(f"[VENO] Using wordlist: {path}", "1;32"))
                    return path
                else:
                    print(color(f"[!] Wordlist not found: {path}", "1;31"))
            else:
                print(color("[!] Invalid choice.", "1;31"))
        except ValueError:
            print(color("[!] Please enter a number.", "1;31"))
