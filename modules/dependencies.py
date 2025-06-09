import shutil
import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---- Try to match VENO's color/console system ----
try:
    from rich.console import Console
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

def color(text, c, bold=False, bg=None):
    codes = {'cyan': '36', 'magenta': '35', 'yellow': '33', 'green': '32', 'red': '31', 'blue': '34', 'white': '37'}
    if not RICH_AVAILABLE:
        style = []
        if bold: style.append('1')
        if c in codes: style.append(codes[c])
        if bg == 'black': style.append('40')
        if not style: style = ['0']
        return f"\033[{';'.join(style)}m{text}\033[0m"
    tag = c
    if bold: tag = f"bold {c}"
    if bg: tag += f" on {bg}"
    return f"[{tag}]{text}[/{tag}]"

# ---- CONSTANTS ----
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
dependencies = list(TOOL_INSTALL_CMDS.keys())
REQUIRED_TOOLS = dependencies
ERROR_LOG = "dependency_error.log"
MAX_THREADS = 8

def log_error(message, output_dir=None):
    """Log installation errors to a file."""
    log_dir = output_dir if output_dir else "."
    err_path = os.path.join(log_dir, ERROR_LOG)
    with open(err_path, "a") as f:
        f.write(message + "\n")

def print_status(msg):
    m = color("[VENO]", "cyan", bold=True) + " " + color(msg, "white")
    if console: console.print(m)
    else: print(m)

def print_success(msg):
    m = color("[✓]", "green", bold=True) + " " + color(msg, "green")
    if console: console.print(m)
    else: print(m)

def print_error(msg):
    m = color("[!]", "red", bold=True, bg="black") + " " + color(msg, "red", bold=True)
    if console: console.print(m)
    else: print(m)

def check_tool(tool):
    """Check if a tool is available in PATH."""
    return tool if shutil.which(tool) is None else None

def check_missing_tools_parallel():
    """Check all required tools in parallel. Returns list of missing."""
    missing = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(check_tool, tool): tool for tool in REQUIRED_TOOLS}
        for future in as_completed(futures):
            result = future.result()
            if result:
                missing.append(result)
    return missing

def install_tool(tool, output_dir=None):
    """Try to install a tool, log errors if it fails."""
    print_status(f"Installing {tool} ...")
    try:
        subprocess.run(TOOL_INSTALL_CMDS[tool], shell=True, check=True)
        print_success(f"{tool} installed.")
    except Exception as e:
        msg = f"Failed to install {tool}: {e}"
        print_error(msg)
        if output_dir:
            log_error(msg, output_dir)
        raise

def check_and_prompt_install(output_dir=None):
    """
    Check all required tools. If missing, prompt user for mass install.
    Fails gracefully and logs to output if install fails.
    """
    missing = check_missing_tools_parallel()
    if not missing:
        return True

    print_error(f"Missing required tools: {', '.join(missing)}")
    if console:
        install_all = console.input(color("Install ALL missing tools automatically? (Y/n):", "yellow", bold=True))
    else:
        install_all = input(color("Install ALL missing tools automatically? (Y/n):", "yellow", bold=True))
    install_all = install_all.strip().lower()
    if install_all not in ["", "y", "yes"]:
        print_error("Required tools missing. Exiting.")
        sys.exit(1)
    failed = []
    for tool in missing:
        try:
            install_tool(tool, output_dir)
        except Exception:
            failed.append(tool)
    if failed:
        print_error(f"Failed to install: {', '.join(failed)}. Exiting.")
        sys.exit(1)
    return True

def check_dependencies(output_dir=None):
    """
    Main entry: checks and installs dependencies as needed.
    Intended to be called from veno.py/main.py.
    """
    check_and_prompt_install(output_dir)
