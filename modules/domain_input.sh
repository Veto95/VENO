#!/bin/bash

validate_domain() {
    local domain="$1"
    if [[ "$domain" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$ ]]; then
        echo "$domain"
    else
        echo ""
    fi
}

load_domains() {
    local domains_file="$1"
    local outdir="$2"
    local error_log="$outdir/error.log"
    if [ ! -f "$domains_file" ] || [ ! -r "$domains_file" ]; then
        echo -e "\033[1;31m[!] File '$domains_file' not found or not readable.\033[0m" | tee -a "$error_log"
        exit 1
    fi
    mapfile -t all_domains < <(grep -v '^#' "$domains_file" | grep . | tr -d '[:space:]' | sort -u)
    if [ ${#all_domains[@]} -eq 0 ]; then
        echo -e "\033[1;31m[!] Domains file is empty.\033[0m" | tee -a "$error_log"
        exit 1
    fi
    local cleaned_domains=()
    for dom in "${all_domains[@]}"; do
        cleaned=$(echo "$dom" | sed 's|https\?://||; s|/.*||; s|^\*\.||')
        validated=$(validate_domain "$cleaned")
        [[ -n "$validated" ]] && cleaned_domains+=("$validated") || echo "Invalid domain skipped: $dom" >> "$error_log"
    done
    if [ ${#cleaned_domains[@]} -eq 0 ]; then
        echo -e "\033[1;31m[!] No valid domains found in file.\033[0m" | tee -a "$error_log"
        exit 1
    fi
    printf "%s\n" "${cleaned_domains[@]}"
}

get_domains() {
    local outdir="$1"
    local error_log="$outdir/error.log"
    local selected_domains=()
    while true; do
        echo -e "\033[1;36m[?] Select how to provide domains:\033[0m"
        echo -e "\033[1;33m  1) Enter domains manually\033[0m"
        echo -e "\033[1;33m  2) Load domains from a file\033[0m"
        read -r -t 60 input_method || {
            echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
            exit 1
        }
        case $input_method in
            1)
                echo -e "\033[1;36m[?] Enter 1-10 domains (space-separated, e.g., example.com):\033[0m"
                read -r -t 60 input || {
                    echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
                    exit 1
                }
                if [ -z "$input" ]; then
                    echo -e "\033[1;31m[!] No domains entered.\033[0m" | tee -a "$error_log"
                    continue
                fi
                IFS=' ' read -r -a domains <<< "$input"
                if [ ${#domains[@]} -gt 10 ]; then
                    echo -e "\033[1;31m[!] Too many domains (${#domains[@]}). Enter 1-10.\033[0m" | tee -a "$error_log"
                    continue
                fi
                valid_domains=()
                for dom in "${domains[@]}"; do
                    validated=$(validate_domain "$dom")
                    if [ -n "$validated" ]; then
                        valid_domains+=("$validated")
                    else
                        echo -e "\033[1;31m[!] Invalid domain: $dom. Skipping.\033[0m" | tee -a "$error_log"
                    fi
                done
                if [ ${#valid_domains[@]} -eq 0 ]; then
                    echo -e "\033[1;31m[!] No valid domains provided.\033[0m" | tee -a "$error_log"
                    continue
                fi
                selected_domains=("${valid_domains[@]}")
                break
                ;;
            2)
                echo -e "\033[1;36m[?] Enter the full path to the domains file:\033[0m"
                read -r -t 60 domains_file || {
                    echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
                    exit 1
                }
                cleaned_domains=($(load_domains "$domains_file" "$outdir"))
                echo -e "\033[1;36m[?] How many domains to scan (1-10)?\033[0m"
                read -r -t 60 domain_count || {
                    echo -e "\033[1;31m[!] Input timed out after 60 seconds.\033[0m" | tee -a "$error_log"
                    exit 1
                }
                if [[ ! "$domain_count" =~ ^[1-9]$|^10$ ]]; then
                    echo -e "\033[1;31m[!] Invalid number. Enter 1 to 10.\033[0m" | tee -a "$error_log"
                    continue
                fi
                if ! command -v fzf &>/dev/null; then
                    echo -e "\033[1;31m[!] fzf not installed. Selecting first $domain_count domains.\033[0m" | tee -a "$error_log"
                    selected_domains=("${cleaned_domains[@]:0:$domain_count}")
                else
                    selected_domains=($(printf "%s\n" "${cleaned_domains[@]}" | timeout -s SIGINT 600 fzf --multi --prompt="Select $domain_count domains: " --height=40% --border --header="Select $domain_count domains"))
                    if [ $? -ne 0 ] || [ "${#selected_domains[@]}" -ne "$domain_count" ]; then
                        echo -e "\033[1;31m[!] Selection failed or incorrect number selected.\033[0m" | tee -a "$error_log"
                        continue
                    fi
                fi
                break
                ;;
            *)
                echo -e "\033[1;31m[!] Invalid choice. Enter '1' or '2'.\033[0m" | tee -a "$error_log"
                ;;
        esac
    done
    printf "%s\n" "${selected_domains[@]}"
}
