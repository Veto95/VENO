"""
VENO Intensity Profiles — Now With Even More Fucking Attitude!
-----------------------------------------------------
Defines scan intensity presets for the VENO recon suite.
Change these if you want to crank it up, tone it down, or just meme.
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
    "light": {
        "description": "Light as fuck — fast, low-noise, skips heavy shit. For sneak peeks only.",
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/quickhits.txt",
        "threads": 5,
        "delay": 0.3,
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
    "medium": {
        "description": "Medium (default): Balanced — solid bug bounty coverage, not too slow, not too cray.",
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/common.txt",
        "threads": 16,
        "delay": 0.8,
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
    "heavy": {
        "description": "Heavy as fuck — melt faces and CPUs. Full arsenal, full send.",
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt",
        "threads": 40,
        "delay": 1.8,
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
    # Add your own custom intensity modes here!
    # "your_custom_profile": {
    #     "description": "Describe your meme mode.",
    #     "wordlist": "/your/meme/list.txt",
    #     ...
    # }
}

# Automatically check wordlists for all profiles on import
for mode, opts in SCAN_INTENSITIES.items():
    _check_wordlist(opts["wordlist"])
