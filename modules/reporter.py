import os
from modules.banner import get_banner_html

def generate_report(domain, config, context):
    outdir = config.get("output_dir") or "output"
    html_report = f"{outdir}/{domain}/report.html"
    banner_html = get_banner_html()

    subdomains = context.get('subdomains', [])
    live_subdomains = context.get('live_subdomains', [])
    sensitive_files = context.get('sensitive_files', [])
    juicy = context.get('juicy', [])
    dir_fuzz = context.get('dir_fuzz', [])
    vuln_urls = context.get('vuln_urls', [])
    nuclei_findings = context.get('nuclei_chained', '')
    scan_stats = [len(subdomains), len(live_subdomains), len(sensitive_files), len(juicy), len(dir_fuzz), len(vuln_urls)]

    with open(html_report, "w", encoding="utf-8") as fout:
        fout.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>VENO Report - {domain}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    :root {{
        --bg-main: #181f2a;
        --bg-card: #232c3b;
        --accent: #2ac3de;
        --accent2: #f7768e;
        --text-main: #e0e5ee;
        --text-faded: #b0b8c1;
        --radius: 14px;
        --shadow: 0 6px 40px #0003;
    }}
    html, body {{
        background: var(--bg-main);
        color: var(--text-main);
        margin: 0; padding: 0;
        font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
    }}
    .header {{
        background: var(--bg-card);
        border-bottom: 2px solid var(--accent);
        position: sticky; top: 0; z-index: 10;
        box-shadow: var(--shadow);
        padding: 0 0 1em 0;
    }}
    .veno-banner {{ 
        margin: 0 auto 1em auto; 
        font-size:clamp(1em,2vw,1.3em);
        display:block; 
        background:transparent;
        color:var(--accent2);
        text-shadow:0 0 8px var(--accent2),0 1px 0 #000;
        border:none;
        padding:0.5em 0 0.5em 0;
    }}
    .main-container {{
        max-width: 1040px;
        margin: 2em auto;
        padding: 1.5em;
        background: var(--bg-card);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        display: flex;
        flex-direction: column;
        gap: 2em;
    }}
    h1 {{
        font-size:2em;
        margin-bottom:0.2em;
        color: var(--accent);
        text-align:center;
        text-shadow: 0 2px 18px var(--accent2);
    }}
    .summary-cards {{
        display: flex;
        flex-wrap: wrap;
        gap: 1.4em;
        justify-content: center;
        margin: 0 0 1em 0;
    }}
    .card {{
        background: #1d2533cc;
        border-radius: var(--radius);
        box-shadow: 0 2px 14px #0006;
        padding: 1.2em 2.1em;
        min-width: 130px;
        flex: 1 1 120px;
        text-align: center;
        transition: transform 0.15s, box-shadow 0.15s;
        border-bottom: 3px solid var(--accent);
    }}
    .card:hover {{
        transform: translateY(-4px) scale(1.03);
        box-shadow: 0 8px 24px var(--accent2), 0 2px 14px #0004;
        border-bottom: 3px solid var(--accent2);
    }}
    .card .count {{ font-size: 2.1em; font-weight: bold; color: var(--accent2); }}
    .card .label {{ color: var(--text-faded); letter-spacing:0.03em; font-size:1em; }}

    .toggle-btn {{
        background: var(--accent2);
        color: #fff;
        border: none;
        padding: 0.55em 1.5em;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1.07em;
        margin: 1em auto 0 auto;
        display:block;
        font-family:inherit;
        box-shadow: 0 1px 5px #0002;
        transition: background 0.18s, color 0.12s, box-shadow 0.18s;
    }}
    .toggle-btn:hover {{
        background: var(--accent);
        color: #222;
        box-shadow: 0 4px 18px var(--accent2);
    }}
    .details {{
        display: none;
        animation: fadeIn 0.4s;
        margin-top: 1.2em;
        gap:2em;
        flex-wrap:wrap;
        justify-content:center;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .section {{
        margin: 0.4em 0 2em 0;
        background: #171e29cc;
        border-radius:var(--radius);
        box-shadow:0 1px 9px #0002;
        padding: 1em 1.5em;
        min-width: 240px;
        max-width: 700px;
    }}
    h2 {{ color: var(--accent2); font-size:1.16em; margin-bottom:0.35em; }}
    pre {{
        background: #232c3b;
        color: var(--text-main);
        border-radius: 8px;
        padding: 1em;
        font-size: 1em;
        overflow-x: auto;
        margin:0;
    }}
    .nuclei-link {{ color: var(--accent); text-decoration: underline; word-break:break-all; }}
    @media (max-width: 800px) {{
        .main-container {{ padding: 0.2em 0.6em; }}
        .summary-cards {{ flex-direction: column; align-items: stretch; }}
        .card {{ min-width: 90px; padding: 0.7em; }}
    }}
</style>
</head>
<body>
<div class="header">
    {banner_html}
</div>
<div class="main-container">
    <h1>VENO Bug Bounty Report: {domain}</h1>
    <div class="summary-cards">
      <div class="card"><div class="count">{len(subdomains)}</div><div class="label">Subdomains</div></div>
      <div class="card"><div class="count">{len(live_subdomains)}</div><div class="label">Live Subs</div></div>
      <div class="card"><div class="count">{len(sensitive_files)}</div><div class="label">Sensitive Files</div></div>
      <div class="card"><div class="count">{len(juicy)}</div><div class="label">Juicy Info</div></div>
      <div class="card"><div class="count">{len(dir_fuzz)}</div><div class="label">Dir Fuzz</div></div>
      <div class="card"><div class="count">{len(vuln_urls)}</div><div class="label">Vuln URLs</div></div>
    </div>
    <canvas id="venoBar" width="840" height="300"></canvas>
    <canvas id="venoPie" width="840" height="170" style="margin-top:2em;"></canvas>
    <button class="toggle-btn" onclick="toggleSection('details')">Show/Hide Details</button>
    <div id="details" class="details" style="display:none;flex-direction:row;">
        <div class="section"><h2>Subdomains</h2><pre>{chr(10).join(subdomains) or 'No subdomains found.'}</pre></div>
        <div class="section"><h2>Live Subdomains</h2><pre>{chr(10).join(live_subdomains) or 'No live subdomains.'}</pre></div>
        <div class="section"><h2>Sensitive Files</h2><pre>{chr(10).join(sensitive_files) or 'No sensitive files found.'}</pre></div>
        <div class="section"><h2>Juicy Info</h2><pre>{chr(10).join(juicy) or 'No juicy info.'}</pre></div>
        <div class="section"><h2>Directory Fuzzing</h2><pre>{chr(10).join(dir_fuzz) or 'No directory fuzzing results.'}</pre></div>
        <div class="section"><h2>Vulnerable URLs</h2><pre>{chr(10).join(vuln_urls) or 'No vulnerable URLs.'}</pre></div>
        <div class="section"><h2>Nuclei Findings</h2>
            <pre>{('<a class="nuclei-link" href="'+nuclei_findings+'">'+nuclei_findings+'</a>') if nuclei_findings else 'None'}</pre>
        </div>
    </div>
</div>
<script>
var ctxBar = document.getElementById('venoBar').getContext('2d');
var ctxPie = document.getElementById('venoPie').getContext('2d');
var barColors = ['#2ac3de','#7dcfff','#f7768e','#9ece6a','#e0def4','#bb9af7'];
var pieColors = ['#2ac3de','#7dcfff','#f7768e','#9ece6a','#e0def4','#bb9af7'];
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
            borderRadius: 8,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            y: {{ beginAtZero: true, grid: {{ color: '#393552' }}, ticks: {{ color: '#e0def4' }} }},
            x: {{ grid: {{ color: '#393552' }}, ticks: {{ color: '#e0def4' }} }}
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
        responsive: true,
        plugins: {{
            legend: {{
                labels: {{ color:'#e0def4', font:{{size:16}} }}
            }}
        }}
    }}
}});
function toggleSection(id) {{
    var el = document.getElementById(id);
    if (el.style.display === "block" || el.style.display === "")
        el.style.display = "none";
    else
        el.style.display = "block";
}}
</script>
</body>
</html>
""")
