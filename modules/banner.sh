#!/bin/bash

banner() {
    local outdir="${1:-.}"
    local error_log="$outdir/error.log"
    mkdir -p "$outdir" 2>>"$error_log" || {
        echo -e "\033[1;31m[!] Failed to create directory $outdir\033[0m" >&2
        echo "Cannot create output directory. Check permissions." >> "$error_log"
        exit 1
    }
    {
        printf "\033[1;32m"
        cat << "EOF"
.-.   .-.,---.  .-. .-. .---.   
 \ \ / / | .-'  |  \| |/ .-. )  
  \ V /  | `-.  |   | || | |(_) 
   ) /   | .-'  | |\  || | | |  
  (_)    |  `--.| | |)|\ `-' /  
         /( __.'/(  (_) )---'   
        (__)   (__)    (_)     

             VENO v1.0
        BUG HUNTING & RECON TOOL

         coder: 0xCACT2S 
 Telegram: HELL SHELL [https://t.me/hacking_hell1]
   GitHub: https://github.com/Veto95/VENO
EOF
        printf "\033[0m\n"
    } 
}
