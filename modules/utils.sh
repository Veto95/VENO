#!/bin/bash

sanitize_domain() {
    local domain="$1"
    local outdir="$2"
    local error_log="$outdir/error.log"
    if [ -z "$domain" ]; then
        echo -e "\033[1;31m[!] Empty domain provided.\033[0m" | tee -a "$error_log"
        exit 1
    fi
    echo "$domain" | tr -dc 'a-zA-Z0-9_-.' | sed 's/\.\{2,\}/_/g; s/^-*//; s/-*$//'
}

timer_start() {
    SECONDS=0
}

timer_end() {
    local duration=$SECONDS
    local outdir="$1"
    echo -e "\033[1;34m[*] Step completed in ${duration}s\033[0m" | tee -a "$outdir/scan.log"
}