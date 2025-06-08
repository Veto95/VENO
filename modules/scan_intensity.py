import os

DEFAULT_OUTPUT_DIR = "output"
DEFAULT_BANNER_HTML = "<h1>VENO Automated Bug Bounty Scan</h1>"

SCAN_INTENSITIES = {
    "fast": {
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
}
