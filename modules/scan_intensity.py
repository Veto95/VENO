def get_scan_intensity(outdir):
    """
    Prompt user for scan intensity with input validation and return config dict.
    """
    print("Select scan intensity:")
    print("  1) Fast (minimal probes, less detail)")
    print("  2) Normal (recommended for most cases)")
    print("  3) Deep (thorough, slow, exhaustive, with WAF evasion)")
    while True:
        choice = input("> ").strip()
        if choice == "1":
            intensity = "fast"
            break
        elif choice == "2":
            intensity = "normal"
            break
        elif choice == "3":
            intensity = "deep"
            break
        else:
            print("\033[1;31m[!] Invalid choice. Enter 1, 2, or 3.\033[0m")

    configs = {
        "fast":   {"intensity": "fast", "threads": 5, "hak_depth": 1, "sqlmap_flags": "", "recursion_depth": 1, "waf_evasion": False},
        "normal": {"intensity": "normal", "threads": 10, "hak_depth": 2, "sqlmap_flags": "--risk=1 --level=1 --random-agent", "recursion_depth": 2, "waf_evasion": False},
        "deep":   {"intensity": "deep", "threads": 20, "hak_depth": 3, "sqlmap_flags": "--risk=3 --level=5 --random-agent --tamper=between,randomcase,space2comment", "recursion_depth": 3, "waf_evasion": True}
    }
    return configs[intensity]

def suggest_tools(scan_config, subdomain_scan):
    """
    Suggest tools based on scan intensity and subdomain scan selection.
    """
    base = []
    if scan_config["intensity"] == "fast":
        base = ["subfinder", "httprobe", "waybackurls"]
    elif scan_config["intensity"] == "deep":
        base = [
            "subfinder", "subjack", "waybackurls", "gau", "hakrawler", "nuclei", "paramspider",
            "arjun", "sqlmap", "ffuf", "dirsearch", "dalfox", "waymore", "uro", "XSStrike"
        ]
    else:  # normal
        base = [
            "subfinder", "subjack", "waybackurls", "gau", "hakrawler", "nuclei", "paramspider",
            "ffuf", "dirsearch", "dalfox"
        ]
    if not subdomain_scan:
        base = [t for t in base if t not in ("subfinder", "subjack")]
    return base
