#!/bin/bash

show_time_in_timezones() {
    declare -A ZONES=(
        ["UTC"]="UTC"
        ["New York"]="America/New_York"
        ["London"]="Europe/London"
        ["Paris"]="Europe/Paris"
        ["Moscow"]="Europe/Moscow"
        ["Beijing"]="Asia/Shanghai"
        ["Tokyo"]="Asia/Tokyo"
        ["Sydney"]="Australia/Sydney"
    )
    for city in "${!ZONES[@]}"; do
        tz="${ZONES[$city]}"
        time=$(TZ=$tz date +"%Y-%m-%d %H:%M:%S")
        echo -e "\033[1;33m$city\033[0m: $time"
    done
}