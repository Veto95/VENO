import json
import os

def save_config(outdir, selected_tools, wordlist, scan_config, recursion_depth, subdomain_scan):
    config = {
        "tools": selected_tools,
        "wordlist": wordlist,
        "scan_config": scan_config,
        "recursion_depth": recursion_depth,
        "subdomain_scan": subdomain_scan
    }
    config_path = os.path.join(outdir, "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
