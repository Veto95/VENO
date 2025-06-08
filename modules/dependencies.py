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
        print("\033[1;32m[✓] All required tools are installed.\033[0m")
        return True
    else:
        print("\033[1;31m[!] Missing required tools:\033[0m", ", ".join(missing))
        for tool in missing:
            install = input(f"\033[1;33mTool '{tool}' is missing. Would you like to install it now? (yes/no):\033[0m ").strip().lower()
            if install in ["yes", "y"]:
                print(f"\033[1;36m[VENO] Installing {tool} ...\033[0m")
                try:
                    subprocess.run(TOOL_INSTALL_CMDS[tool], shell=True, check=True)
                except Exception as e:
                    print(f"\033[1;31m[!] Failed to install {tool}: {e}\033[0m")
                    print("\033[1;31m[!] Exiting.\033[0m")
                    sys.exit(1)
            else:
                print(f"\033[1;31m[!] {tool} is required. Exiting.\033[0m")
                sys.exit(1)
        print("\033[1;32m[✓] All required tools are now installed.\033[0m")
        return True

def check_dependencies(output_dir=None):
    check_and_prompt_install()
