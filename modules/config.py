import os

DEFAULT_OUTPUT_DIR = "output"
DEFAULT_BANNER_HTML = "<h1>VENO Automated Bug Bounty Scan</h1>"

# ---- WORDLISTS ----
WORDLISTS = {
    "quick": "/usr/share/seclists/Discovery/Web-Content/quickhits.txt",
    "common": "/usr/share/seclists/Discovery/Web-Content/common.txt",
    "raft-medium": "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
    "raft-large": "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt",
    "big": "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt",
    "param": "/usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt",
    # Add more as needed
}

SCAN_INTENSITIES = {
    "low": {
        "wordlist": WORDLISTS["quick"],
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
        "per_tool_wordlists": {
            "directory_fuzzing": WORDLISTS["quick"],
            "param_discovery": WORDLISTS["param"]
        }
    },
    "medium": {
        "wordlist": WORDLISTS["common"],
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
        "per_tool_wordlists": {
            "directory_fuzzing": WORDLISTS["common"],
            "param_discovery": WORDLISTS["param"]
        }
    },
    "high": {
        "wordlist": WORDLISTS["raft-medium"],
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
        "per_tool_wordlists": {
            "directory_fuzzing": WORDLISTS["raft-medium"],
            "param_discovery": WORDLISTS["param"]
        }
    },
    "max": {
        "wordlist": WORDLISTS["raft-large"],
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
        "per_tool_wordlists": {
            "directory_fuzzing": WORDLISTS["raft-large"],
            "param_discovery": WORDLISTS["param"]
        }
    }
}

def get_config(
    domain,
    output_dir=DEFAULT_OUTPUT_DIR,
    scan_intensity="medium",
    banner_html=DEFAULT_BANNER_HTML,
    custom_wordlist=None,
    per_tool_wordlists=None
):
    """
    Returns a config dict compatible with scanner_steps.py and context passing.
    Supports global and per-tool wordlist overrides!
    """
    intensity = SCAN_INTENSITIES.get(scan_intensity, SCAN_INTENSITIES["medium"])

    # Allow user to override global wordlist and/or per-tool wordlists
    wl = custom_wordlist or intensity["wordlist"]
    per_tool_wl = intensity.get("per_tool_wordlists", {}).copy()
    if per_tool_wordlists:
        per_tool_wl.update(per_tool_wordlists)  # User overrides

    config = {
        "output_dir": output_dir,
        "wordlist": wl,
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
            "per_tool_wordlists": per_tool_wl
        },
        "banner_html": banner_html,
        "domain": domain
    }
    return config

# Example usage in main.py or scanner.py:
# from modules.config import get_config, WORDLISTS
# config = get_config(domain="example.com", scan_intensity="high", custom_wordlist=WORDLISTS["big"])
# config2 = get_config(domain="foo.com", per_tool_wordlists={"directory_fuzzing": "/path/to/mylist.txt"})
