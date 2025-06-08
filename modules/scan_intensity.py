def get_scan_intensity(outdir):
    print("Select scan intensity:")
    print("  1) Fast (minimal probes, less detail)")
    print("  2) Normal (recommended for most cases)")
    print("  3) Deep (thorough, slow, exhaustive)")
    choice = input("> ").strip()
    if choice == "1":
        intensity = "fast"
    elif choice == "3":
        intensity = "deep"
    else:
        intensity = "normal"
    # You can extend/modify the below as needed
    if intensity == "fast":
        config = {"intensity": "fast", "threads": 5, "hak_depth": 1, "sqlmap_flags": "", "recursion_depth": 1}
    elif intensity == "deep":
        config = {"intensity": "deep", "threads": 20, "hak_depth": 3, "sqlmap_flags": "--risk=3 --level=5", "recursion_depth": 3}
    else:
        config = {"intensity": "normal", "threads": 10, "hak_depth": 2, "sqlmap_flags": "--risk=1 --level=1", "recursion_depth": 2}
    return config

def suggest_tools(scan_config):
    """Suggest appropriate tools for the scan intensity"""
    if scan_config["intensity"] == "fast":
        return [
            "subfinder", "httprobe", "waybackurls"
        ]
    elif scan_config["intensity"] == "deep":
        return [
            "subfinder", "subjack", "waybackurls", "gau", "hakrawler", "nuclei", "paramspider",
            "arjun", "sqlmap", "ffuf", "dirsearch", "dalfox", "waymore", "uro", "xsstrike"
        ]
    else:  # normal
        return [
            "subfinder", "subjack", "waybackurls", "gau", "hakrawler", "nuclei", "paramspider",
            "ffuf", "dirsearch", "dalfox"
        ]
