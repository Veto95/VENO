#!/bin/bash
set -euo pipefail

# Source all helper modules (fail fast if missing)
for mod in modules/*.sh; do
    if [[ ! -f "$mod" ]]; then
        echo -e "\033[1;31m[!] Missing required module: $mod\033[0m" >&2
        exit 1
    fi
    source "$mod"
done

main() {
    mkdir -p output
    local outdir="output"
    banner "$outdir"
    check_dependencies "$outdir"

    local selected_domains
    selected_domains=($(get_domains "$outdir"))

    # Structured config retrieval
    local scan_config scan_intensity threads hak_depth sqlmap_flags wordlist recursion_depth
    scan_config=$(get_scan_intensity "$outdir")
    eval "$scan_config"

    local subdomain_scan
    subdomain_scan=$(get_subdomain_scan_choice "$outdir")

    wordlist=$(get_wordlist "$wordlist" "$outdir")

    local selected_tools
    selected_tools=$(get_tool_selection "$outdir")

    save_config "$outdir" "$selected_tools" "$wordlist" "$scan_config" "$recursion_depth" "$subdomain_scan"

    touch "$outdir/scanned_domains.txt" "$outdir/scanned_ips.txt" 2>>"$outdir/error.log"

    for domain in "${selected_domains[@]}"; do
        if ! scan_domain "$domain" "$outdir" "$threads" "$hak_depth" "$sqlmap_flags" "$wordlist" "$selected_tools" "$recursion_depth" "$subdomain_scan"; then
            echo -e "\033[1;31m[!] Scan failed for $domain. See $outdir/$domain/errors.log for details.\033[0m" >&2
        fi
    done

    echo -e "\033[1;32m[\u2713] Scan completed. Check $outdir for results.\033[0m"
}

trap 'echo -e "\033[1;31m[!] Script terminated unexpectedly. Check error logs in output directory.\033[0m" >&2; exit 1' ERR
main
