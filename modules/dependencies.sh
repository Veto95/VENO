#!/bin/bash

detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        echo "apt"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    elif command -v brew >/dev/null 2>&1; then
        echo "brew"
    else
        echo "none"
    fi
}

check_dependencies() {
    local outdir="$1"
    local error_log="$outdir/error.log"
    local script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
    local REQUIRED_TOOLS=(
        fzf theHarvester subjack waybackurls nuclei paramspider gf arjun sqlmap ffuf
        dirsearch dalfox waymore uro curl pandoc hakrawler naabu gau httprobe parallel
        subfinder xsstrike jq dig
    )
    local python_tools=("theHarvester" "paramspider" "arjun" "sqlmap" "dirsearch" "dalfox" "xsstrike")
    local go_tools=("subjack" "waybackurls" "nuclei" "ffuf" "waymore" "uro" "gau" "httprobe" "subfinder")
    local installed_flag="$script_dir/.dependencies_installed"
    local missing_tools=()
    local pkg_manager=$(detect_package_manager)

    echo -e "\033[1;33m[*] Checking for required tools...\033[0m"
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -eq 0 ]; then
        echo -e "\033[1;32m[✓] All required tools are installed.\033[0m"
        touch "$installed_flag" 2>>"$error_log" || echo "Warning: Could not create $installed_flag" >> "$error_log"
        return
    fi

    echo -e "\033[1;31m[!] Missing tools: ${missing_tools[*]}\033[0m"
    echo -e "\033[1;33m[*] Attempting to install missing tools...\033[0m"

    if [ "$pkg_manager" = "none" ]; then
        echo -e "\033[1;31m[!] No supported package manager found (apt, yum, brew).\033[0m" >&2
        echo "Install tools manually: ${missing_tools[*]}" >> "$error_log"
        exit 1
    fi

    # Install pip if missing
    if ! command -v pip &>/dev/null; then
        echo -e "\033[1;33m[*] Installing pip...\033[0m"
        case $pkg_manager in
            apt) sudo apt update && sudo apt install -y python3-pip ;;
            yum) sudo yum install -y python3-pip ;;
            brew) brew install python ;;
        esac 2>>"$error_log" || {
            echo "Failed to install pip" >> "$error_log"
            exit 1
        }
    fi

    # Install Go if missing for Go tools
    if ! command -v go &>/dev/null && [ ${#go_tools[@]} -gt 0 ]; then
        echo -e "\033[1;33m[*] Installing Go...\033[0m"
        case $pkg_manager in
            apt) sudo apt update && sudo apt install -y golang ;;
            yum) sudo yum install -y golang ;;
            brew) brew install go ;;
        esac 2>>"$error_log" || echo "Warning: Failed to install Go; skipping Go-based tools" >> "$error_log"
    fi

    for tool in "${missing_tools[@]}"; do
        if [[ " ${python_tools[*]} " =~ " $tool " ]]; then
            echo -e "\033[1;33m[*] Installing $tool via pip...\033[0m"
            python3 -m pip install "$tool" --user 2>>"$error_log" || echo "Failed to install $tool via pip" >> "$error_log"
        elif [[ " ${go_tools[*]} " =~ " $tool " ]]; then
            if command -v go &>/dev/null; then
                echo -e "\033[1;33m[*] Installing $tool via go install...\033[0m"
                case $tool in
                    subjack) go install github.com/haccer/subjack@latest ;;
                    waybackurls) go install github.com/tomnomnom/waybackurls@latest ;;
                    nuclei) go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest ;;
                    ffuf) go install github.com/ffuf/ffuf@latest ;;
                    waymore) go install github.com/xnl-h4ck3r/waymore@latest ;;
                    uro) go install github.com/s0md3v/uro@latest ;;
                    gau) go install github.com/lc/gau@latest ;;
                    httprobe) go install github.com/tomnomnom/httprobe@latest ;;
                    subfinder) go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest ;;
                esac 2>>"$error_log" || echo "Failed to install $tool via go" >> "$error_log"
            else
                echo -e "\033[1;31m[!] Go not installed. Skipping $tool.\033[0m"
            fi
        else
            echo -e "\033[1;33m[*] Installing $tool via $pkg_manager...\033[0m"
            case $pkg_manager in
                apt) sudo apt update && sudo apt install -y "$tool" ;;
                yum) sudo yum install -y "$tool" ;;
                brew) brew install "$tool" ;;
            esac 2>>"$error_log" || echo "Failed to install $tool via $pkg_manager" >> "$error_log"
        fi
    done

    # Verify installation
    missing_tools=()
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -eq 0 ]; then
        touch "$installed_flag" 2>>"$error_log" || echo "Warning: Could not create $installed_flag" >> "$error_log"
        echo -e "\033[1;32m[✓] All tools installed successfully.\033[0m"
    else
        echo -e "\033[1;31m[!] Failed to install: ${missing_tools[*]}. Install manually.\033[0m" >&2
        echo "Remaining missing tools: ${missing_tools[*]}" >> "$error_log"
        exit 1
    fi
}