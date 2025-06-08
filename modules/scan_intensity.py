def get_scan_intensity(outdir):
    print("Select scan intensity:")
    print("  1) Fast (minimal probes, less detail)")
    print("  2) Normal (recommended for most cases)")
    print("  3) Deep (thorough, slow, exhaustive, with WAF evasion)")
    choice = input("> ").strip()
    if choice == "1":
        intensity = "fast"
    elif choice == "3":
        intensity = "deep"
    else:
        intensity = "normal"
    if intensity == "fast":
        config = {"intensity": "fast", "threads": 5, "hak_depth": 1, "sqlmap_flags": "", "recursion_depth": 1, "waf_evasion": False}
    elif intensity == "deep":
        config = {
            "intensity": "deep",
            "threads": 20,
            "hak_depth": 3,
            "sqlmap_flags": "--risk=3 --level=5 --random-agent --tamper=between,randomcase,space2comment",
            "recursion_depth": 3,
            "waf_evasion": True
        }
    else:
        config = {
            "intensity": "normal",
            "threads": 10,
            "hak_depth": 2,
            "sqlmap_flags": "--risk=1 --level=1 --random-agent",
            "recursion_depth": 2,
            "waf_evasion": False
        }
    return config

def suggest_tools(scan_config, subdomain_scan):
    base = []
    if scan_config["intensity"] == "fast":
        base = ["subfinder", "httprobe", "waybackurls"]
    elif scan_config["intensity"] == "deep":
        base = [
            "subfinder", "subjack", "waybackurls", "gau", "hakrawler", "nuclei", "paramspider",
            "arjun", "sqlmap", "ffuf", "dirsearch", "dalfox", "waymore", "uro", "xsstrike"
        ]
    else:  # normal
        base = [
            "subfinder", "subjack", "waybackurls", "gau", "hakrawler", "nuclei", "paramspider",
            "ffuf", "dirsearch", "dalfox"
        ]
    if not subdomain_scan and "subfinder" in base:
        base.remove("subfinder")
    if not subdomain_scan and "subjack" in base:
        base.remove("subjack")
    return base
