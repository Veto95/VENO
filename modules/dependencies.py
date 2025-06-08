import subprocess

REQUIRED_TOOLS = [
    "fzf", "theHarvester", "subjack", "waybackurls", "nuclei", "paramspider",
    "gf", "arjun", "sqlmap", "ffuf", "dirsearch", "dalfox", "waymore", "uro",
    "curl", "pandoc", "hakrawler", "naabu", "gau", "httprobe", "parallel",
    "subfinder", "xsstrike", "jq", "dig"
]

def check_dependencies(outdir):
    error_log = f"{outdir}/error.log"
    missing_tools = []
    for tool in REQUIRED_TOOLS:
        if subprocess.call(["which", tool], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            missing_tools.append(tool)

    if missing_tools:
        with open(error_log, "a") as f:
            f.write(f"Missing tools: {' '.join(missing_tools)}\n")
        print(f"\033[1;31m[!] Missing required tools: {', '.join(missing_tools)}\033[0m")
        print("Install them and re-run this script.")
        exit(1)
    else:
        print("\033[1;32m[\u2713] All required tools are installed.\033[0m")
