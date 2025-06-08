from modules.wordlist import get_wordlist, COMMON_WORDLISTS

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
    }
}

def get_config(
    domain,
    output_dir=DEFAULT_OUTPUT_DIR,
    scan_intensity="medium",
    banner_html=DEFAULT_BANNER_HTML
):
    """
    Returns a config dict for VENO pipeline, per-intensity, with wordlist selector.
    """
    # Prompt user for wordlist (env override or interactive)
    wordlist_path = get_wordlist(output_dir)
    intensity = SCAN_INTENSITIES.get(scan_intensity, SCAN_INTENSITIES["medium"])

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

# Example usage in main.py or scanner.py:
# from modules.config import get_config
# config = get_config(domain="example.com", scan_intensity="high")
