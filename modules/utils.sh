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
generate_html_report() {
    local domain="$1"
    local outdir="$2"
    local sanitized_domain
    sanitized_domain=$(sanitize_domain "$domain" "$outdir")
    local report="$outdir/${sanitized_domain}/report.html"
    local scan_date=$(date '+%Y-%m-%d %H:%M:%S')

    # Count findings for graph data
    local subdomains_count=0
    local params_count=0
    local xss_count=0
    local sqli_count=0
    local takeover_count=0

    [[ -f "$outdir/$sanitized_domain/subdomains.txt" ]] && subdomains_count=$(wc -l < "$outdir/$sanitized_domain/subdomains.txt")
    [[ -f "$outdir/$sanitized_domain/paramspider.txt" ]] && params_count=$(wc -l < "$outdir/$sanitized_domain/paramspider.txt")
    [[ -f "$outdir/$sanitized_domain/dalfox.txt" ]] && xss_count=$(grep -i "vulnerable\|[xX][sS][sS]" "$outdir/$sanitized_domain/dalfox.txt" | wc -l)
    [[ -f "$outdir/$sanitized_domain/sqlmap.txt" ]] && sqli_count=$(grep -i "sql injection" "$outdir/$sanitized_domain/sqlmap.txt" | wc -l)
    [[ -f "$outdir/$sanitized_domain/subjack.txt" ]] && takeover_count=$(grep -i "vulnerable" "$outdir/$sanitized_domain/subjack.txt" | wc -l)

    cat > "$report" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VENO Scan Report: $domain</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #fafafa; margin: 0; padding: 0; }
.container { max-width: 900px; margin: 30px auto; background: #222242; border-radius: 14px; box-shadow: 0 4px 30px #0006; padding: 32px 40px; }
h1, h2, h3 { color: #00ffd0; }
.summary { background: #14142b; padding: 16px; border-radius: 8px; margin-bottom: 24px; }
a { color: #40c4ff; text-decoration: underline; }
pre { background: #191933; padding: 10px; border-radius: 6px; overflow-x: auto; }
.tool-section { margin-bottom: 34px; }
.severity-critical { color: #ff1744; font-weight: bold; }
.severity-high { color: #ff9100; }
.severity-medium { color: #ffe082; }
.severity-low { color: #00e676; }
.footer { margin-top: 40px; color: #888; font-size: 0.95em; }
@media (max-width: 600px) {
    .container { padding: 12px 5px; }
}
</style>
</head>
<body>
<div class="container">
<h1>VENO Bug Hunting Report</h1>
<div class="summary">
    <h2>Summary for <span style="color:#40c4ff;">$domain</span></h2>
    <ul>
        <li><b>Scan date:</b> $scan_date</li>
        <li><b>Output folder:</b> $outdir/$sanitized_domain</li>
    </ul>
    <canvas id="graphFindings" height="130"></canvas>
    <script>
        const ctx = document.getElementById('graphFindings').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Subdomains', 'Parameters', 'XSS', 'SQLi', 'Takeover'],
                datasets: [{
                    label: 'Findings',
                    data: [$subdomains_count, $params_count, $xss_count, $sqli_count, $takeover_count],
                    backgroundColor: [
                        '#00ffd0cc', '#40c4ffcc', '#ffeb3bcc', '#ff1744cc', '#ff9100cc'
                    ],
                    borderColor: [
                        '#00ffd0', '#40c4ff', '#ffeb3b', '#ff1744', '#ff9100'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, ticks: { color: '#fff' } },
                    x: { ticks: { color: '#fff' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    </script>
</div>
EOF

    # List tool sections
    for tool in theHarvester subjack waybackurls nuclei ffuf dirsearch dalfox sqlmap; do
        local file="$outdir/$sanitized_domain/$tool.txt"
        if [[ -f "$file" ]]; then
            echo "<div class=\"tool-section\">" >> "$report"
            echo "<h2>${tool^} Results</h2>" >> "$report"
            echo "<a href=\"$tool.txt\" target=\"_blank\">Download raw output</a>" >> "$report"
            echo "<pre>" >> "$report"
            head -50 "$file" >> "$report"
            echo "</pre>" >> "$report"
            echo "</div>" >> "$report"
        fi
    done

    # Add more sections as needed (JS files, sensitive info, errors...)
    if [[ -f "$outdir/$sanitized_domain/errors.log" ]]; then
        echo "<h3 style=\"color:#ff5252\">Recent Errors</h3><pre>" >> "$report"
        tail -20 "$outdir/$sanitized_domain/errors.log" >> "$report"
        echo "</pre>" >> "$report"
    fi

    cat >> "$report" <<EOF
<div class="footer">
    <hr>
    <i>Generated by VENO | <a href="https://t.me/hacking_hell1" target="_blank">HELL SHELL Telegram</a></i>
</div>
</div>
</body>
</html>
EOF
}
