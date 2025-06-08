import shutil
import subprocess
import sys

TOOL_INSTALL_CMDS = {
    "theHarvester": "sudo apt install -y theharvester",
    "subfinder": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "subjack": "go install github.com/haccer/subjack@latest",
    "waybackurls": "go install github.com/tomnomnom/waybackurls@latest",
    "nuclei": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
    "paramspider": "pip install paramspider",
    "gf": "go install github.com/tomnomnom/gf@latest",
    "arjun": "pip install arjun",
    "sqlmap": "sudo apt install -y sqlmap",
    "ffuf": "go install github.com/ffuf/ffuf/v2@latest",
    "dirsearch": "git clone https://github.com/maurosoria/dirsearch.git && cd dirsearch && pip install -r requirements.txt",
    "dalfox": "go install github.com/hahwul/dalfox/v2@latest",
    "waymore": "pip install waymore",
    "uro": "pip install uro",
    "curl": "sudo apt install -y curl",
    "pandoc": "sudo apt install -y pandoc",
    "hakrawler": "go install github.com/hakluke/hakrawler@latest",
    "naabu": "go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest",
    "gau": "go install github.com/lc/gau/v2/cmd/gau@latest",
    "httprobe": "go install github.com/tomnomnom/httprobe@latest",
    "parallel": "sudo apt install -y parallel",
    "xsstrike": "pip install xsstrike",
    "jq": "sudo apt install -y jq",
    "dig": "sudo apt install -y dnsutils",
    "fzf": "sudo apt install -y fzf",
}

REQUIRED_TOOLS = list(TOOL_INSTALL_CMDS.keys())

def check_and_prompt_install():
    missing = []
    for tool in REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            missing.append(tool)
    if not missing:
        print("[✓] All required tools are installed.")
        return True
    else:
        print("[!] Missing required tools:", ", ".join(missing))
        for tool in missing:
            install = input(f"Tool '{tool}' is missing. Would you like to install it now? (yes/no): ").strip().lower()
            if install in ["yes", "y"]:
                print(f"[VENO] Installing {tool} ...")
                try:
                    subprocess.run(TOOL_INSTALL_CMDS[tool], shell=True, check=True)
                except Exception as e:
                    print(f"[!] Failed to install {tool}: {e}")
                    print("[!] Exiting.")
                    sys.exit(1)
            else:
                print(f"[!] {tool} is required. Exiting.")
                sys.exit(1)
        print("[✓] All required tools are now installed.")
        return True
