"""
VENO Intensity Profiles
-----------------------
Defines scan intensity presets for the VENO recon suite.
Edit these bad boys if you want different wordlists, thread counts, or tool combos.

"""

import os

# Where all output files go by default
DEFAULT_OUTPUT_DIR = "output"
# Banner for the HTML report, customize or meme as desired
DEFAULT_BANNER_HTML = "<h1>VENO Automated Bug Bounty Scan</h1>"

def _check_wordlist(path):
    """Warn if the wordlist is missing, but don't be a dick and crash."""
    if not os.path.isfile(path):
        print(f"\033[1;33m[WARNING]\033[0m Wordlist not found: {path} — you might be about to eat shit!")

SCAN_INTENSITIES = {
    "fast": {
        # Super quick, for when you just wanna spray and pray
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/quickhits.txt",
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
    },
    "normal": {
        # Your bread-and-butter scan, not too fast, not too slow
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/common.txt",
        "threads": 20,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": False,
        "dir_fuzz_tool": "ffuf",
        "gau": True,
        "dalfox": True,
        "xsstrike": False,
    },
    "deep": {
        # For when you want to melt the target and your CPU
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt",
        "threads": 50,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": True,
        "dir_fuzz_tool": "dirsearch",
        "gau": True,
        "dalfox": True,
        "xsstrike": True,
    },
    # Example: add your own custom profile here
    # "your_custom_mode": {
    #     "wordlist": "/path/to/your/wordlist.txt",
    #     "threads": 100,
    #     "run_subjack": True,
    #     "run_sqlmap": True,
    #     ...
    # }
}

# Automatically check wordlists for all profiles on import
for mode, opts in SCAN_INTENSITIES.items():
    _check_wordlist(opts["wordlist"])
