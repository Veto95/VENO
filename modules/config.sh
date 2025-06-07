#!/bin/bash

get_scan_intensity() {
    local outdir="$1"
    local error_log="$outdir/error.log"
    while true; do
        echo -e "\033[1;36m[?] Select scan intensity:\033[0m"
        echo -e "\033[1;33m  1) Light: Fast, basic checks\033[0m"
        echo -e "\033[1;33m  2) Medium: Balanced speed and coverage\033[0m"
        echo -e "\033[1;33m  3) Heavy: Slow, in-depth scans\033[0m"
        read -r -t 60 intensity || {
            echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
            exit 1
        }
        case $intensity in
            1) echo "threads=50 hak_depth=2 sqlmap_flags='--batch --random-agent' wordlist='/usr/share/wordlists/raft-medium-directories.txt' recursion_depth=1"; break;;
            2) echo "threads=100 hak_depth=3 sqlmap_flags='--batch --random-agent --level=3 --risk=2 --tamper=space2comment' wordlist='/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt' recursion_depth=2"; break;;
            3) echo "threads=200 hak_depth=5 sqlmap_flags='--batch --random-agent --level=5 --risk=3 --tamper=space2comment,charunicodeencode' wordlist='/usr/share/wordlists/dirbuster/directory-list-larges.txt' recursion_depth=3"; break;;
            *) echo -e "\033[1;31m[!] Invalid choice. Enter '1', '2', or '3'.\033[0m" | tee -a "$error_log";;
        esac
    done
}

get_subdomain_scan_choice() {
    local outdir="$1"
    local error_log="$outdir/error.log"
    while true; do
        echo -e "\033[1;36m[?] Do you want to scan subdomains?\033[0m"
        echo -e "\033[1;33m  1) No: Scan only main domain(s)\033[0m"
        echo -e "\033[1;33m  2) Yes, non-recursive: Scan subdomains\033[0m"
        echo -e "\033[1;33m  3) Yes, recursive: Scan subdomains and their subdomains\033[0m"
        read -r -t 60 choice || {
            echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
            exit 1
        }
        case $choice in
            1) echo "no"; break;;
            2) echo "non_recursive"; break;;
            3) echo "recursive"; break;;
            *) echo -e "\033[1;31m[!] Invalid choice. Enter '1', '2', or '3'.\033[0m" | tee -a "$error_log";;
        esac
    done
}

get_wordlist() {
    local default_wordlist="$1"
    local outdir="$2"
    local error_log="$outdir/error.log"
    echo -e "\033[1;36m[?] Specify a wordlist for directory scanning (Enter for default: $default_wordlist):\033[0m"
    read -r -t 60 custom_wordlist || {
        echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
        exit 1
    }
    if [ -n "$custom_wordlist" ] && [ -f "$custom_wordlist" ] && [ -r "$custom_wordlist" ]; then
        echo "$custom_wordlist"
    else
        echo -e "\033[1;33m[*] Using default wordlist: $default_wordlist\033[0m" | tee -a "$error_log"
        echo "$default_wordlist"
    fi
}

get_tool_selection() {
    local outdir="$1"
    local error_log="$outdir/error.log"
    local available_tools=("subfinder" "theHarvester" "subjack" "waybackurls" "extract_sensitive" "grep_juicy" "paramspider" "nuclei" "ffuf" "dirsearch" "dalfox" "sqlmap" "xsstrike")
    echo -e "\033[1;36m[?] Select tools to run (space-separated, e.g., ffuf dirsearch):\033[0m"
    echo -e "\033[1;33m  Press Enter for all: ${available_tools[*]}\033[0m"
    read -r -t 60 tool_input || {
        echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
        exit 1
    }
    if [ -z "$tool_input" ]; then
        echo "${available_tools[*]}"
    else
        local selected_tools=()
        IFS=' ' read -r -a input_tools <<< "$tool_input"
        for tool in "${input_tools[@]}"; do
            if [[ " ${available_tools[*]} " =~ " $tool " ]]; then
                selected_tools+=("$tool")
            else
                echo -e "\033[1;31m[!] Invalid tool: $tool. Ignoring.\033[0m" | tee -a "$error_log"
            fi
        done
        if [ ${#selected_tools[@]} -eq 0 ]; then
            echo -e "\033[1;33m[*] No valid tools selected. Using all tools.\033[0m" | tee -a "$error_log"
            echo "${available_tools[*]}"
        else
            echo "${selected_tools[*]}"
        fi
    fi
}

save_config() {
    local outdir="$1"
    local selected_tools="$2"
    local wordlist="$3"
    local intensity="$4"
    local recursion_depth="$5"
    local subdomain_scan="$6"
    local config_file="$outdir/veno_config.json"
    local error_log="$outdir/error.log"

    if [ ! -w "$outdir" ]; then
        echo -e "\033[1;31m[!] Output directory $outdir is not writable.\033[0m" | tee -a "$error_log"
        exit 1
    fi

    cat << EOF > "$config_file" 2>>"$error_log"
{
  "tools": "$selected_tools",
  "wordlist": "$wordlist",
  "intensity": "$intensity",
  "recursion_depth": "$recursion_depth",
  "subdomain_scan": "$subdomain_scan"
}
EOF
    if [ $? -eq 0 ]; then
        echo -e "\033[1;32m[\u2713] Configuration saved to $config_file\033[0m"
    else
        echo -e "\033[1;31m[!] Failed to save config to $config_file\033[0m" | tee -a "$error_log"
        exit 1
    fi
}
