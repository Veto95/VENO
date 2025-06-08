from modules.wordlist import COMMON_WORDLISTS
import os

DEFAULT_OUTPUT_DIR = "output"
DEFAULT_BANNER_HTML = "<h1>VENO Automated Bug Bounty Scan</h1>"

SCAN_INTENSITIES = {
    "low": {
        "threads": 5,
        "run_subjack": False,
        "run_sqlmap": False,
        "run_waymore": False,
        "run_hakrawler": False,
        "run_nuclei_full": False,
        "dir_fuzz_tool": "ffuf",
        "gau": False,
        "dalfox": False,
        "xsstrike": False,
        "default_wordlist": COMMON_WORDLISTS["SecLists: Discovery/Web-Content/common.txt"],
    },
    "medium": {
        "threads": 10,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": False,
        "dir_fuzz_tool": "ffuf",
        "gau": True,
        "dalfox": True,
        "xsstrike": False,
        "default_wordlist": COMMON_WORDLISTS["SecLists: Discovery/Web-Content/big.txt"],
    },
    "high": {
        "threads": 40,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": True,
        "dir_fuzz_tool": "ffuf",
        "gau": True,
        "dalfox": True,
        "xsstrike": True,
        "default_wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
    },
    "max": {
        "threads": 100,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": True,
        "dir_fuzz_tool": "dirsearch",
        "gau": True,
        "dalfox": True,
        "xsstrike": True,
        "default_wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt",
    }
}

def prompt_wordlist(default_wordlist):
    # Check env first (automation/headless mode)
    env_wordlist = os.environ.get("VENO_WORDLIST")
    if env_wordlist and os.path.isfile(env_wordlist):
        print(f"\033[1;32m[VENO] Using wordlist from VENO_WORDLIST: {env_wordlist}\033[0m")
        return env_wordlist

    # Interactive selection
    print("\033[1;36m\n[VENO] Wordlist Selection\033[0m")
    print("\033[1;37mAvailable wordlists:\033[0m")
    for idx, (desc, path) in enumerate(COMMON_WORDLISTS.items(), 1):
        print(f"\033[1;33m  {idx}: {desc} ({path})\033[0m")
    print("\033[1;35m  0: Enter custom path\033[0m")
    print(f"\033[1;32m  (Just press enter to use default for this scan intensity: {default_wordlist})\033[0m")

    while True:
        choice = input("\033[1;34mSelect wordlist [0/1/2/3 or ENTER for default]: \033[0m")
        if choice.strip() == "":
            print(f"\033[1;32m[VENO] Using default wordlist for this scan intensity: {default_wordlist}\033[0m")
            return default_wordlist
        try:
            choice = int(choice)
            if choice == 0:
                path = input("\033[1;35mEnter full path to your wordlist: \033[0m").strip()
                if os.path.isfile(path):
                    print(f"\033[1;32m[VENO] Using custom wordlist: {path}\033[0m")
                    return path
                else:
                    print("\033[1;31m[!] File not found. Try again.\033[0m")
            elif 1 <= choice <= len(COMMON_WORDLISTS):
                path = list(COMMON_WORDLISTS.values())[choice - 1]
                if os.path.isfile(path):
                    print(f"\033[1;32m[VENO] Using wordlist: {path}\033[0m")
                    return path
                else:
                    print(f"\033[1;31m[!] Wordlist not found: {path}\033[0m")
            else:
                print("\033[1;31m[!] Invalid choice.\033[0m")
        except ValueError:
            print("\033[1;31m[!] Please enter a number or just ENTER for default.\033[0m")

def get_config(
    domain,
    output_dir=DEFAULT_OUTPUT_DIR,
    scan_intensity="medium",
    banner_html=DEFAULT_BANNER_HTML
):
    intensity = SCAN_INTENSITIES.get(scan_intensity, SCAN_INTENSITIES["medium"])
    wordlist_path = prompt_wordlist(intensity["default_wordlist"])

    config = {
        "output_dir": output_dir,
        "wordlist": wordlist_path,
        "scan_intensity": scan_intensity,
        "scan_config": {
            "threads": intensity["threads"],
            "dir_fuzz_tool": intensity["dir_fuzz_tool"],
            "run_subjack": intensity["run_subjack"],
            "run_sqlmap": intensity["run_sqlmap"],
            "run_waymore": intensity["run_waymore"],
            "run_hakrawler": intensity["run_hakrawler"],
            "run_nuclei_full": intensity["run_nuclei_full"],
            "gau": intensity["gau"],
            "dalfox": intensity["dalfox"],
            "xsstrike": intensity["xsstrike"],
        },
        "banner_html": banner_html,
        "domain": domain
    }
    return config

# Example usage:
# from modules.config import get_config
# config = get_config(domain="example.com", scan_intensity="high")
