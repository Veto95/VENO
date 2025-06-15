
# reporter.py — The Ultimate Hacker-Themed Scan Report Generator
# Fully loaded with Chart.js graphs, status badges, collapsible sections,
# JSON viewer & download, sidebar nav, fuzzy path sorting, SQLMap injection detail,
# and dark-mode hacker aesthetics.

import os
import json
import datetime
from collections import defaultdict

# === Utility functions ===

def safe_get(d, key, default=None):
    return d[key] if key in d else default

def status_badge(status):
    return {
        "success": "✅",
        "warning": "⚠️",
        "fail": "❌",
        "skip": "⏭️",
    }.get(status.lower(), "❓")

def escape_html(text):
    import html
    return html.escape(str(text))

def iso_timestamp():
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

# === HTML Snippets ===

HEADER = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>🔥 VENO Hacker Scan Report</title>
    <style>
        body {
            background: #0d1117; 
            color: #c9d1d9;
            font-family: "Fira Code", monospace, monospace;
            margin: 0; padding: 0; 
        }
        a, a:visited { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* Sidebar nav */
        #sidebar {
            position: fixed; top: 0; left: 0;
            width: 280px; height: 100vh;
            background: rgba(20, 26, 33, 0.95);
            border-right: 1px solid #21262d;
            padding: 20px;
            overflow-y: auto;
            transition: transform 0.3s ease;
            z-index: 9999;
        }
        #sidebar.hide {
            transform: translateX(-300px);
        }
        #sidebar h2 {
            margin-top: 0;
            font-weight: 700;
            font-size: 1.4em;
            letter-spacing: 1.5px;
            color: #58a6ff;
            margin-bottom: 1em;
        }
        #sidebar ul {
            list-style: none;
            padding-left: 0;
            font-size: 0.9em;
        }
        #sidebar ul li {
            margin-bottom: 0.8em;
        }
        #sidebar ul li a {
            color: #8b949e;
            cursor: pointer;
        }
        #sidebar ul li a:hover {
            color: #58a6ff;
        }

        /* Main content */
        #content {
            margin-left: 300px;
            padding: 20px;
            max-width: 1200px;
        }

        /* Toggle button */
        #toggleSidebarBtn {
            position: fixed;
            top: 10px; left: 10px;
            background: #238636;
            border: none;
            color: #fff;
            padding: 8px 14px;
            cursor: pointer;
            font-size: 1em;
            z-index: 10000;
            border-radius: 4px;
            box-shadow: 0 0 10px #238636aa;
        }
        #toggleSidebarBtn:hover {
            background: #2ea043;
        }

        /* Section styling */
        section {
            margin-bottom: 3rem;
            border-radius: 10px;
            background: #161b22cc;
            padding: 1.5rem;
            box-shadow: 0 0 15px #23863666;
        }

        h1, h2, h3 {
            color: #58a6ff;
            text-shadow: 0 0 8px #58a6ff88;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 0.2rem;
        }

        h2 {
            font-size: 1.8rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        h3 {
            font-size: 1.2rem;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }

        /* Collapsible */
        details {
            background: #0d1117;
            border-radius: 6px;
            margin-bottom: 1rem;
            box-shadow: inset 0 0 10px #23863633;
            padding: 0.75rem 1rem;
        }
        details[open] {
            box-shadow: 0 0 20px #238636bb;
        }
        summary {
            font-weight: 700;
            cursor: pointer;
            user-select: none;
            color: #58a6ff;
        }

        /* Tables */
        table {
            border-collapse: collapse;
            width: 100%;
            color: #c9d1d9;
        }
        th, td {
            border: 1px solid #30363d;
            padding: 8px;
            text-align: left;
            font-family: "Fira Code", monospace, monospace;
        }
        th {
            background-color: #21262d;
        }
        tr:nth-child(even) {
            background-color: #161b22;
        }

        /* Status badge */
        .badge {
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.85rem;
            display: inline-block;
            min-width: 30px;
            text-align: center;
            user-select: none;
        }
        .badge-success { background-color: #238636; color: #d2f8d2; }
        .badge-warning { background-color: #e3b341; color: #392f00; }
        .badge-fail { background-color: #cf222e; color: #f8d7d7; }
        .badge-skip { background-color: #6a737d; color: #e1e4e8; }

        /* JSON viewer */
        #jsonviewer {
            background: #010409;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.9rem;
            overflow: auto;
            max-height: 400px;
            padding: 1rem;
            box-shadow: 0 0 20px #238636aa inset;
            white-space: pre-wrap;
        }

        /* Chart container */
        .chart-container {
            width: 100%;
            height: 300px;
            margin: 1rem 0;
        }

        /* Fuzz path highlight */
        .fuzz-path {
            font-family: monospace;
            background: #23863622;
            border-radius: 5px;
            padding: 0.2em 0.5em;
            user-select: text;
        }

        /* Glow icon */
        .icon-glow {
            filter: drop-shadow(0 0 6px #58a6ffaa);
            vertical-align: middle;
        }
    </style>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <button id="toggleSidebarBtn">☰ Menu</button>
    <nav id="sidebar" class="">
        <h2>🔥 VENO Report</h2>
        <ul id="navList">
            <!-- dynamically populated -->
        </ul>
    </nav>
    <main id="content">
'''

FOOTER = '''
    </main>

    <script>
        // Sidebar toggle
        const sidebar = document.getElementById('sidebar');
        const toggleBtn = document.getElementById('toggleSidebarBtn');
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('hide');
        });

        // Smooth scroll for nav links
        document.querySelectorAll('#navList a').forEach(anchor => {
            anchor.addEventListener('click', e => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if(target) target.scrollIntoView({behavior: 'smooth'});
            });
        });

        // Auto collapse empty details
        document.querySelectorAll('details').forEach(d => {
            if(d.textContent.trim() === '' || d.querySelectorAll('*').length === 0) {
                d.style.display = 'none';
            }
        });
    </script>
</body>
</html>
'''

# === Main reporter class ===

class Reporter:
    def __init__(self, output_path, report_data):
        """
        output_path: str path to write the report HTML
        report_data: dict parsed scan data context
        """
        self.output_path = output_path
        self.data = report_data

        # Section order and titles for sidebar nav
        self.sections = [
            ("summary", "Summary"),
            ("vulnerabilities", "Vulnerabilities"),
            ("sqlmap", "SQLMap Injections"),
            ("fuzzing", "Fuzzing Results"),
            ("sensitive", "Sensitive Data Found"),
            ("graphs", "Graphs & Analytics"),
            ("raw_json", "Raw JSON Data"),
            ("tool_status", "Tool Status"),
        ]

    def generate_report(self):
        html = HEADER
        html += f'<h1>🔥 VENO Hacker Scan Report</h1>\n'
        html += f'<p>Generated at: {iso_timestamp()}</p>\n'
        
        # Sidebar nav placeholders, will inject later
        nav_links = []

        # Content container to fill sections
        content_html = ''

        # Iterate sections to generate content
        for sec_id, sec_title in self.sections:
            section_html = self._render_section(sec_id, sec_title)
            if section_html:
                content_html += f'<section id="{sec_id}">\n<h2>{sec_title}</h2>\n{section_html}\n</section>\n'
                nav_links.append(f'<li><a href="#{sec_id}">{sec_title}</a></li>')

        # Insert nav links dynamically
        nav_html = '\n'.join(nav_links)
        html = html.replace('<ul id="navList">\n    <!-- dynamically populated -->\n  </ul>', f'<ul id="navList">\n{nav_html}\n</ul>')

        html += content_html
        html += FOOTER

        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'[VENO REPORT] Report generated at: {self.output_path}')

    # Section renderers
    def _render_section(self, sec_id, sec_title):
        if sec_id == "summary":
            return self._render_summary()
        elif sec_id == "vulnerabilities":
            return self._render_vulnerabilities()
        elif sec_id == "sqlmap":
            return self._render_sqlmap()
        elif sec_id == "fuzzing":
            return self._render_fuzzing()
        elif sec_id == "sensitive":
            return self._render_sensitive()
        elif sec_id == "graphs":
            return self._render_graphs()
        elif sec_id == "raw_json":
            return self._render_raw_json()
        elif sec_id == "tool_status":
            return self._render_tool_status()
        else:
            return ''

    def _render_summary(self):
        d = self.data.get('summary', {})
        if not d:
            return '<p>No summary data found.</p>'
        
        html = f'''
            <p><strong>Domain:</strong> {escape_html(d.get("domain", "N/A"))}</p>
            <p><strong>Scan started:</strong> {escape_html(d.get("start_time", "N/A"))}</p>
            <p><strong>Scan finished:</strong> {escape_html(d.get("end_time", "N/A"))}</p>
            <p><strong>Scan duration:</strong> {escape_html(d.get("duration", "N/A"))}</p>
            <p><strong>Total vulnerabilities found:</strong> {escape_html(d.get("vuln_count", 0))}</p>
            <p><strong>Total sensitive data matches:</strong> {escape_html(d.get("sensitive_count", 0))}</p>
        '''
        return html

    def _render_vulnerabilities(self):
        vulns = self.data.get('vulnerabilities', [])
        if not vulns:
            return '<p>No vulnerabilities detected.</p>'

        # Group by severity for easy scan
        severity_groups = defaultdict(list)
        for v in vulns:
            sev = v.get('severity', 'unknown').lower()
            severity_groups[sev].append(v)

        html = ''
        for sev in ['critical', 'high', 'medium', 'low', 'unknown']:
            group = severity_groups.get(sev, [])
            if not group:
                continue
            badge = status_badge('fail' if sev in ['critical', 'high'] else 'warning' if sev == 'medium' else 'success')
            html += f'<h3>{sev.capitalize()} Vulnerabilities {badge}</h3>'
            for v in group:
                name = escape_html(v.get('name', 'Unnamed Vuln'))
                desc = escape_html(v.get('description', ''))
                url = escape_html(v.get('url', ''))
                param = escape_html(v.get('param', ''))
                evidence = escape_html(v.get('evidence', ''))
                html += f'''
                    <details>
                        <summary>{name} — Target: {url} — Param: {param}</summary>
                        <p><em>{desc}</em></p>
                        <p><strong>Evidence:</strong> {evidence}</p>
                    </details>
                '''
        return html

    def _render_sqlmap(self):
        sqlmap = self.data.get('sqlmap', {})
        if not sqlmap or not sqlmap.get('injections'):
            return '<p>No SQLMap injection data found.</p>'
        
        injections = sqlmap['injections']
        html = ''
        for inj in injections:
            url = escape_html(inj.get('url', 'N/A'))
            param = escape_html(inj.get('parameter', 'N/A'))
            techniques = inj.get('techniques', [])
            status = inj.get('status', 'unknown')
            badge = status_badge(status)
            html += f'<details><summary>Injection on {url} — Param: {param} {badge}</summary>'
            html += '<ul>'
            for tech in techniques:
                tech_name = escape_html(tech.get('name', 'unknown'))
                tech_success = tech.get('success', False)
                tech_status = 'success' if tech_success else 'fail'
                tech_badge = status_badge(tech_status)
                html += f'<li>{tech_name} {tech_badge}</li>'
            html += '</ul></details>'
        return html

    def _render_fuzzing(self):
        fuzz = self.data.get('fuzzing', [])
        if not fuzz:
            return '<p>No fuzzing results found.</p>'
        
        # Sort by status (success > warning > fail) and path alphabetically
        status_rank = {'success': 0, 'warning': 1, 'fail': 2, 'skip': 3, 'unknown': 4}
        sorted_fuzz = sorted(fuzz, key=lambda x: (status_rank.get(x.get('status', 'unknown').lower(), 99), x.get('path', '')))

        html = '<table><thead><tr><th>Path</th><th>Status</th><th>Response Code</th><th>Length</th><th>Notes</th></tr></thead><tbody>'
        for entry in sorted_fuzz:
            path = escape_html(entry.get('path', ''))
            status = entry.get('status', 'unknown').lower()
            badge_class = f'badge-{status}' if status in ['success', 'warning', 'fail', 'skip'] else ''
            badge = status_badge(status)
            code = escape_html(entry.get('response_code', ''))
            length = escape_html(entry.get('response_length', ''))
            notes = escape_html(entry.get('notes', ''))
            html += f'<tr><td class="fuzz-path">{path}</td><td class="badge {badge_class}">{badge} {status.capitalize()}</td><td>{code}</td><td>{length}</td><td>{notes}</td></tr>'
        html += '</tbody></table>'
        return html

    def _render_sensitive(self):
        sensitive = self.data.get('sensitive', [])
        if not sensitive:
            return '<p>No sensitive data found.</p>'
        
        html = '<table><thead><tr><th>Type</th><th>Match</th><th>Location</th></tr></thead><tbody>'
        for item in sensitive:
            typ = escape_html(item.get('type', ''))
            match = escape_html(item.get('match', ''))
            loc = escape_html(item.get('location', ''))
            html += f'<tr><td>{typ}</td><td>{match}</td><td>{loc}</td></tr>'
        html += '</tbody></table>'
        return html

    def _render_graphs(self):
        # Prepare JS data
        vulns = self.data.get('vulnerabilities', [])
        vuln_counts = defaultdict(int)
        for v in vulns:
            sev = v.get('severity', 'unknown').capitalize()
            vuln_counts[sev] += 1

        fuzz = self.data.get('fuzzing', [])
        fuzz_status_counts = defaultdict(int)
        for f in fuzz:
            status = f.get('status', 'unknown').capitalize()
            fuzz_status_counts[status] += 1

        sensitive = self.data.get('sensitive', [])
        sensitive_types = defaultdict(int)
        for s in sensitive:
            t = s.get('type', 'Unknown')
            sensitive_types[t] += 1

        # Chart.js scripts and canvases
        html = '''
            <div class="chart-container">
                <canvas id="vulnSeverityChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="fuzzStatusChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="sensitiveTypesChart"></canvas>
            </div>

            <script>
                const vulnSeverityCtx = document.getElementById('vulnSeverityChart').getContext('2d');
                const vulnSeverityChart = new Chart(vulnSeverityCtx, {
                    type: 'doughnut',
                    data: {
                        labels: {vuln_labels},
                        datasets: [{
                            label: 'Vulnerabilities by Severity',
                            data: {vuln_data},
                            backgroundColor: ['#cf222e', '#f85149', '#d29922', '#238636', '#8b949e'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: '#c9d1d9',
                                    font: { size: 14, family: 'Fira Code, monospace' }
                                }
                            }
                        }
                    }
                });

                const fuzzStatusCtx = document.getElementById('fuzzStatusChart').getContext('2d');
                const fuzzStatusChart = new Chart(fuzzStatusCtx, {
                    type: 'bar',
                    data: {
                        labels: {fuzz_labels},
                        datasets: [{
                            label: 'Fuzzing Status',
                            data: {fuzz_data},
                            backgroundColor: ['#238636', '#e3b341', '#cf222e', '#6a737d', '#8b949e']
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { color: '#c9d1d9' }
                            },
                            x: {
                                ticks: { color: '#c9d1d9' }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: { color: '#c9d1d9' }
                            }
                        }
                    }
                });

                const sensitiveTypesCtx = document.getElementById('sensitiveTypesChart').getContext('2d');
                const sensitiveTypesChart = new Chart(sensitiveTypesCtx, {
                    type: 'pie',
                    data: {
                        labels: {sens_labels},
                        datasets: [{
                            label: 'Sensitive Data Types',
                            data: {sens_data},
                            backgroundColor: [
                                '#238636', '#cf222e', '#f85149', '#d29922', '#6a737d',
                                '#58a6ff', '#b392f0', '#2ea043', '#d16ba5'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: { color: '#c9d1d9' }
                            }
                        }
                    }
                });
            </script>
        '''.format(
            vuln_labels=json.dumps(list(vuln_counts.keys())),
            vuln_data=json.dumps(list(vuln_counts.values())),
            fuzz_labels=json.dumps(list(fuzz_status_counts.keys())),
            fuzz_data=json.dumps(list(fuzz_status_counts.values())),
            sens_labels=json.dumps(list(sensitive_types.keys())),
            sens_data=json.dumps(list(sensitive_types.values()))
        )
        return html

    def _render_raw_json(self):
        json_data = json.dumps(self.data, indent=2)
        html = f'''
            <div id="jsonviewer">{escape_html(json_data)}</div>
        '''
        return html

    def _render_tool_status(self):
        tools = self.data.get('tool_status', {})
        if not tools:
            return '<p>No tool status data found.</p>'
        
        html = '<table><thead><tr><th>Tool</th><th>Status</th><th>Version</th><th>Notes</th></tr></thead><tbody>'
        for tool, info in tools.items():
            status = info.get('status', 'unknown').lower()
            badge_class = f'badge-{status}' if status in ['success', 'warning', 'fail', 'skip'] else ''
            badge = status_badge(status)
            version = escape_html(info.get('version', 'N/A'))
            notes = escape_html(info.get('notes', ''))
            html += f'<tr><td>{escape_html(tool)}</td><td class="badge {badge_class}">{badge} {status.capitalize()}</td><td>{version}</td><td>{notes}</td></tr>'
        html += '</tbody></table>'
        return html

# === Top-level wrapper for scanner_steps.py compatibility ===
def generate_report(output_path, report_data):
    """
    Wrapper function to expose Reporter.generate_report for module-level import.
    
    Args:
        output_path (str): Path to write the report HTML
        report_data (dict): Parsed scan data context
    """
    reporter = Reporter(output_path, report_data)
    reporter.generate_report()

# === Usage example ===
# Assuming you have scan data in a dict `scan_data` and want to save to output.html:
#
# from modules.reporter import generate_report
# generate_report("output.html", scan_data)
