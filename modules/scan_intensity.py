import os

DEFAULT_OUTPUT_DIR = "output"
DEFAULT_BANNER_HTML = "<h1>VENO Automated Bug Bounty Scan</h1>"

SCAN_INTENSITIES = {
    "low": {
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
    "medium": {
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/common.txt",
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
    },
    "high": {
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
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
    },
    "max": {
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt",
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
    }
}

def get_config(
    domain,
    output_dir=DEFAULT_OUTPUT_DIR,
    scan_intensity="medium",
    banner_html=DEFAULT_BANNER_HTML
):
    """
    Returns a config dict compatible with scanner_steps.py and context passing.
    """
    intensity = SCAN_INTENSITIES.get(scan_intensity, SCAN_INTENSITIES["medium"])

    config = {
        "output_dir": output_dir,
        "wordlist": intensity["wordlist"],
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
        "domain": domain,
    }
    return config

# Example usage in main.py or scanner.py:
# from modules.config import get_config
# config = get_config(domain="example.com", scan_intensity="high")
