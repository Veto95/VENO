
# modules/reporter.py

def generate_report(domain, config, context):
    outdir = config.get("output_dir") or "output"
    html_report = f"{outdir}/{domain}/report.html"
    banner_html = "<pre style='font-size:1.6em;color:#50fa7b;'>VENO BANNER HERE</pre>"

    subdomains = context.get('subdomains', [])
    live_subdomains = context.get('live_subdomains', [])
    sensitive_files = context.get('sensitive_files', [])
    juicy = context.get('juicy', [])
    dir_fuzz = context.get('dir_fuzz', [])
    vuln_urls = context.get('vuln_urls', [])
    nuclei_findings = context.get('nuclei_chained', '')
    scan_stats = [len(subdomains), len(live_subdomains), len(sensitive_files), len(juicy), len(dir_fuzz), len(vuln_urls)]

    with open(html_report, "w", encoding="utf-8") as fout:
        html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VENO Report - {domain}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    body {{ background:#191724; color:#e0def4; font-family:'Fira Mono','Consolas',monospace; margin:0; padding:0; }}
    .container {{ max-width:950px; margin:2em auto; background:#232136; border-radius:18px; box-shadow:0 0 40px #000a; padding:2em 3em 3em 3em; }}
    h1,h2 {{ color:#f6c177; text-shadow:0 2px 8px #e0def477; }}
    ul {{ font-size:1.1em; line-height:1.7; }}
    pre {{ background:#26233a; color:#e0def4; border-radius:8px; padding:1em; font-size:1em; overflow:auto; }}
    .section {{ margin-top:2em; }}
    .details {{ display:none; margin-top:1em; }}
    .toggle-btn {{ background:#31748f; color:#fff; border:none; padding:0.45em 1.1em; border-radius:6px; cursor:pointer; font-size:1em; margin-bottom:1em; }}
    .toggle-btn:hover {{ background:#9ccfd8; color:#232136; }}
    .nuclei-link {{ color:#eb6f92; text-decoration:underline; }}
</style>
</head>
<body>
<div class="container">
{banner_html}
<h1>VENO Bug Bounty Report: {domain}</h1>
<canvas id="venoBar" width="870" height="360"></canvas>
<canvas id="venoPie" width="870" height="200" style="margin-top:2em;"></canvas>
<ul>
    <li>Subdomains found: <b>{len(subdomains)}</b></li>
    <li>Live subdomains: <b>{len(live_subdomains)}</b></li>
    <li>Sensitive files: <b>{len(sensitive_files)}</b></li>
    <li>Juicy info: <b>{len(juicy)}</b></li>
    <li>Directory fuzzing: <b>{len(dir_fuzz)}</b></li>
    <li>Vulnerable URLs: <b>{len(vuln_urls)}</b></li>
    <li>Nuclei findings: <b>{('<a class="nuclei-link" href="'+nuclei_findings+'">'+nuclei_findings+'</a>') if nuclei_findings else 'None'}</b></li>
</ul>
<button class="toggle-btn" onclick="toggleSection('details')">Show/Hide All Details</button>
<div id="details" class="details">
    <div class="section">
        <h2>Subdomains</h2>
        <pre>{chr(10).join(subdomains) or 'No subdomains found.'}</pre>
    </div>
    <div class="section">
        <h2>Live Subdomains</h2>
        <pre>{chr(10).join(live_subdomains) or 'No live subdomains.'}</pre>
    </div>
    <div class="section">
        <h2>Sensitive Files</h2>
        <pre>{chr(10).join(sensitive_files) or 'No sensitive files found.'}</pre>
    </div>
    <div class="section">
        <h2>Juicy Info</h2>
        <pre>{chr(10).join(juicy) or 'No juicy info.'}</pre>
    </div>
    <div class="section">
        <h2>Directory Fuzzing</h2>
        <pre>{chr(10).join(dir_fuzz) or 'No directory fuzzing results.'}</pre>
    </div>
    <div class="section">
        <h2>Vulnerable URLs</h2>
        <pre>{chr(10).join(vuln_urls) or 'No vulnerable URLs.'}</pre>
    </div>
</div>
</div>
<script>
var ctxBar = document.getElementById('venoBar').getContext('2d');
var ctxPie = document.getElementById('venoPie').getContext('2d');
var barColors = ['#c4a7e7','#9ccfd8','#ebbcba','#f6c177','#e0def4','#ea9a97'];
var pieColors = ['#31748f','#a3be8c','#eb6f92','#f6c177','#9ccfd8','#e0def4'];

new Chart(ctxBar, {{
    type: 'bar',
    data: {{
        labels: ['Subdomains','Live Subs','Sensitive','Juicy','Dir Fuzz','Vuln URLs'],
        datasets: [{{
            label: 'Findings',
            data: {scan_stats},
            backgroundColor: barColors,
            borderColor: '#232136',
            borderWidth: 2,
            borderRadius: 7,
        }}]
    }},
    options: {{
        plugins: {{
            legend: {{ display: false }}
        }},
        scales: {{
            y: {{
                beginAtZero: true,
                grid: {{ color: '#393552' }},
                ticks: {{ color: '#e0def4' }},
            }},
            x: {{
                grid: {{ color: '#393552' }},
                ticks: {{ color: '#e0def4' }},
            }}
        }}
    }}
}});

new Chart(ctxPie, {{
    type: 'pie',
    data: {{
        labels: ['Subdomains','Live Subs','Sensitive','Juicy','Dir Fuzz','Vuln URLs'],
        datasets: [{{
            data: {scan_stats},
            backgroundColor: pieColors,
            borderColor: '#191724',
            borderWidth: 2,
        }}]
    }},
    options: {{
        plugins: {{
            legend: {{
                labels: {{ color:'#e0def4', font:{{size:16}} }}
            }}
        }}
    }}
}});

function toggleSection(id) {{
    var el = document.getElementById(id);
    el.style.display = (el.style.display === "block") ? "none" : "block";
}}
</script>
</body>
</html>
"""
        fout.write(html_code)
