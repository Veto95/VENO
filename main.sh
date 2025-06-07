# main.sh
#!/bin/bash
set -o pipefail

# Source all helper modules (ensure these exist in your modules directory)
for mod in modules/*.sh; do source "$mod"; done

main() {
    mkdir -p output
    local outdir="output"
    banner "$outdir"
    check_dependencies "$outdir"

    local selected_domains=($(get_domains "$outdir"))
    local scan_intensity=$(get_scan_intensity "$outdir")
    eval "$scan_intensity"
    local subdomain_scan=$(get_subdomain_scan_choice "$outdir")
    local wordlist=$(get_wordlist "$wordlist" "$outdir")
    local selected_tools=$(get_tool_selection "$outdir")
    save_config "$outdir" "$selected_tools" "$wordlist" "$intensity" "$recursion_depth" "$subdomain_scan"

    touch "$outdir/scanned_domains.txt" "$outdir/scanned_ips.txt" 2>>"$outdir/error.log"
    for domain in "${selected_domains[@]}"; do
        scan_domain "$domain" "$outdir" "$threads" "$hak_depth" "$sqlmap_flags" "$wordlist" "$selected_tools" "$recursion_depth" "$subdomain_scan"
    done
    echo -e "\033[1;32m[✓] Scan completed. Check $outdir for results.\033[0m"
}

trap 'echo -e "\033[1;31m[!] Script terminated unexpectedly. Check error logs in output directory.\033[0m" >&2; exit 1' ERR
main
