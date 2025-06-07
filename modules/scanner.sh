#!/bin/bash

scan_domain() {
    local domain="$1"
    local outdir="$2"
    local threads="$3"
    local hak_depth="$4"
    local sqlmap_flags="$5"
    local wordlist="$6"
    local selected_tools="$7"
    local recursion_depth="$8"
    local subdomain_scan="$9"
    local sanitized_domain
    sanitized_domain=$(sanitize_domain "$domain" "$outdir")
    local error_log="$outdir/$sanitized_domain/errors.log"

    echo -e "\n\033[1;33m[*] Starting scan for $domain\033[0m" | tee -a "$outdir/scan.log"
    mkdir -p "$outdir/$sanitized_domain" 2>>"$error_log" || {
        echo "Failed to create directory $outdir/$sanitized_domain" >> "$error_log"
        return 1
    }

    # Subdomain enumeration
    if [[ " $selected_tools " =~ " subfinder " ]]; then
        enumerate_subdomains "$domain" "$outdir" "$selected_tools" "$recursion_depth" 1 "$subdomain_scan"
    fi

    # theHarvester
    if [[ " $selected_tools " =~ " theHarvester " ]]; then
        echo -e "\033[1;36m[+] Running theHarvester for $domain\033[0m" | tee -a "$outdir/scan.log"
        timer_start
        if ! command -v theHarvester &>/dev/null; then
            echo "theHarvester not installed" >> "$error_log"
        else
            timeout -s SIGINT 600 theHarvester -d "$domain" -b all -f "$outdir/$sanitized_domain/harvest.html" > /dev/null 2>>"$error_log"
            if [ $? -ne 0 ]; then
                echo "theHarvester failed or timed out for $domain" >> "$error_log"
            fi
        fi
        timer_end "$outdir"
    fi

    # subjack
    if [[ " $selected_tools " =~ " subjack " ]]; then
        echo -e "\033[1;36m[+] Running subjack for $domain\033[0m" | tee -a "$outdir/scan.log"
        timer_start
        if ! command -v subjack &>/dev/null; then
            echo "subjack not installed" >> "$error_log"
        else
            timeout -s SIGINT 600 subjack -w <(echo "$domain") -t "$threads" -timeout 30 -o "$outdir/$sanitized_domain/subjack.txt" -ssl > /dev/null 2>>"$error_log"
            if [ $? -ne 0 ]; then
                echo "subjack failed or timed out for $domain" >> "$error_log"
            fi
        fi
        timer_end "$outdir"
    fi

    # waybackurls
    if [[ " $selected_tools " =~ " waybackurls " ]]; then
        echo -e "\033[1;36m[+] Running waybackurls for $domain\033[0m" | tee -a "$outdir/scan.log"
        timer_start
        if ! command -v waybackurls &>/dev/null; then
            echo "waybackurls not installed" >> "$error_log"
        else
            echo "$domain" | timeout -s SIGINT 600 waybackurls > "$outdir/$sanitized_domain/waybackurls.txt" 2>>"$error_log"
            if [ $? -ne 0 ]; then
                echo "waybackurls failed or timed out for $domain" >> "$error_log"
            fi
        fi
        timer_end "$outdir"
    fi

    # Sensitive files
    if [[ " $selected_tools " =~ " extract_sensitive " ]]; then
        extract_sensitive_files "$domain" "$outdir" "$selected_tools"
    fi

    # Juicy info and JS files
    if [[ " $selected_tools " =~ " grep_juicy " ]]; then
        extract_juicy_info "$domain" "$outdir" "$selected_tools"
        extract_js_files "$domain" "$outdir" "$selected_tools"
    fi

    # Parameter discovery
    if [[ " $selected_tools " =~ " paramspider " ]]; then
        discover_parameters "$domain" "$outdir" "$selected_tools"
    fi

    # nuclei
    if [[ " $selected_tools " =~ " nuclei " ]]; then
        echo -e "\033[1;36m[+] Updating nuclei templates\033[0m" | tee -a "$outdir/scan.log"
        timer_start
        if ! command -v nuclei &>/dev/null; then
            echo "nuclei not installed" >> "$error_log"
        else
            timeout -s SIGINT 600 nuclei -update-templates > /dev/null 2>>"$error_log"
            if [ $? -eq 0 ]; then
                echo -e "\033[1;36m[+] Running nuclei for $domain\033[0m" | tee -a "$outdir/scan.log"
                timeout -s SIGINT 600 nuclei -u "$domain" -severity critical,high -o "$outdir/$sanitized_domain/nuclei.txt" > /dev/null 2>>"$error_log"
                if [ $? -ne 0 ]; then
                    echo "nuclei failed or timed out for $domain" >> "$error_log"
                fi
            else
                echo "nuclei update failed or timed out for $domain" >> "$error_log"
            fi
        fi
        timer_end "$outdir"
    fi

    # ffuf
    if [[ " $selected_tools " =~ " ffuf " ]]; then
        scan_ffuf "$domain" "$outdir" "$wordlist" "$selected_tools"
    fi

    # dirsearch
    if [[ " $selected_tools " =~ " dirsearch " ]]; then
        scan_dirsearch "$domain" "$outdir" "$wordlist" "$selected_tools"
    fi

    # XSS scan
    if [[ " $selected_tools " =~ " dalfox " || " $selected_tools " =~ " xsstrike " ]]; then
        run_xss_scan "$domain" "$outdir" "$selected_tools"
    fi

    # SQLmap
    if [[ " $selected_tools " =~ " sqlmap " ]]; then
        run_sqlmap "$domain" "$outdir" "$selected_tools" "$sqlmap_flags"
    fi

    # HTML Report
    generate_html_report "$domain" "$outdir"
}