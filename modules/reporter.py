import os
import time
import logging
import html
from datetime import datetime

try:
    from rich.console import Console
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def color(text, c, bold=False, bg=None):
    if not RICH_AVAILABLE:
        codes = {
            'cyan': '36', 'magenta': '35', 'yellow': '33', 'green': '32',
            'red': '31', 'blue': '34', 'white': '37'
        }
        style = []
        if bold: style.append('1')
        if c in codes: style.append(codes[c])
        if bg == 'black': style.append('40')
        if not style: style = ['0']
        return f"\033[{';'.join(style)}m{text}\033[0m"
    tag = c
    if bold: tag = f"bold {c}"
    if bg: tag += f" on {bg}"
    return f"[{tag}]{text}[/{tag}]"

def safe_read_file(filepath, max_lines=100, error_log=None):
    """Read file content safely, limiting lines to avoid memory issues."""
    if not os.path.isfile(filepath):
        return None
    try:
        lines = []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append("... (truncated, see full file for details)")
                    break
                lines.append(html.escape(line.strip()))
        return lines
    except Exception as e:
        if error_log:
            with open(error_log, 'a', encoding='utf-8') as ferr:
                ferr.write(f"Failed to read {filepath}: {e}\n")
        logger.error(f"Failed to read {filepath}: {e}")
        return None

def generate_report(domain, config, context):
    """Generate an HTML report summarizing scan results."""
    start_time = time.time()
    output_dir = os.path.abspath(config.get('output_dir', 'output'))
    intensity = config.get('intensity', 'medium')
    domain_dir = os.path.join(output_dir, domain)
    error_log = os.path.join(domain_dir, 'errors.log')
    report_file = os.path.join(domain_dir, 'report.html')

    # Ensure output directory exists
    try:
        os.makedirs(domain_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory {domain_dir}: {e}")
        if console:
            console.print(color(f"[VENO] Failed to create output directory: {e}", 'red', bold=True))
        return

    # Collect summary data
    summary = {
        'subdomains': len(context.get('subdomains', [])),
        'live_subdomains': len(context.get('live_subdomains', [])),
        'wayback_urls': 0,
        'sensitive_files': len(context.get('sensitive_files', [])),
        'juicy_info': len(context.get('juicy', [])),
        'vuln_urls': len(context.get('vuln_urls', [])),
        'xss_files': len(context.get('xss', [])),
        'dir_fuzz': len(context.get('dir_fuzz', [])),
        'sqlmap_scans': len(context.get('sqlmap', [])),
        'nuclei_findings': 0,
        'failures': len(context.get('failures', []))
    }

    # Count wayback URLs
    wayback_file = context.get('waybackurls', os.path.join(domain_dir, 'waybackurls.txt'))
    if os.path.isfile(wayback_file):
        try:
            with open(wayback_file, 'r', encoding='utf-8', errors='ignore') as f:
                summary['wayback_urls'] = sum(1 for _ in f)
        except Exception as e:
            logger.error(f"Failed to count lines in {wayback_file}: {e}")

    # Count Nuclei findings
    nuclei_file = context.get('nuclei_chained', os.path.join(domain_dir, 'nuclei_chained.txt'))
    if os.path.isfile(nuclei_file):
        try:
            with open(nuclei_file, 'r', encoding='utf-8', errors='ignore') as f:
                summary['nuclei_findings'] = sum(1 for _ in f)
        except Exception as e:
            logger.error(f"Failed to count lines in {nuclei_file}: {e}")

    # Read file contents for detailed sections
    files_to_read = {
        'Subdomains': os.path.join(domain_dir, 'all_subdomains.txt'),
        'Live Subdomains': os.path.join(domain_dir, 'live_subdomains.txt'),
        'Wayback URLs': wayback_file,
        'Sensitive Files': os.path.join(domain_dir, 'sensitive_files.txt'),
        'Juicy Info': os.path.join(domain_dir, 'juicy_info.txt'),
        'Vulnerable URLs': os.path.join(domain_dir, 'paramspider.txt'),
        'Directory Fuzzing': os.path.join(domain_dir, 'dir_fuzz.txt'),
        'Nuclei Findings': nuclei_file,
    }
    file_contents = {key: safe_read_file(path, max_lines=100, error_log=error_log) for key, path in files_to_read.items()}
    
    # XSS files
    xss_contents = []
    for xss_file in context.get('xss', []):
        if os.path.isfile(xss_file):
            content = safe_read_file(xss_file, max_lines=50, error_log=error_log)
            xss_contents.append((os.path.basename(xss_file), content))

    # SQLMap logs
    sqlmap_logs = [(os.path.basename(log), os.listdir(log) if os.path.isdir(log) else []) for log in context.get('sqlmap', [])]

    # Generate HTML report
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VENO Scan Report - {html.escape(domain)}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        function toggleSection(id) {{
            const section = document.getElementById(id);
            section.classList.toggle('hidden');
        }}
        function downloadReport() {{
            const content = document.documentElement.outerHTML;
            const blob = new Blob([content], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'veno_report_{domain}.html';
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
</head>
<body class="bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-sans">
    <nav class="bg-blue-600 p-4 shadow-md">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold text-white">VENO Scan Report</h1>
            <button onclick="downloadReport()" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
                Download Report
            </button>
        </div>
    </nav>
    <div class="container mx-auto p-6">
        <h2 class="text-3xl font-bold mb-4">Scan Report for {html.escape(domain)}</h2>
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-2">Scan Metadata</h3>
            <p><strong>Domain:</strong> {html.escape(domain)}</p>
            <p><strong>Intensity:</strong> {html.escape(intensity)}</p>
            <p><strong>Output Directory:</strong> {html.escape(output_dir)}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>VENO Version:</strong> 1.0</p>
        </div>
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-2">Summary</h3>
            <table class="w-full table-auto border-collapse">
                <thead>
                    <tr class="bg-gray-200 dark:bg-gray-700">
                        <th class="border px-4 py-2">Category</th>
                        <th class="border px-4 py-2">Count</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Subdomains</td><td>{summary['subdomains']}</td></tr>
                    <tr><td>Live Subdomains</td><td>{summary['live_subdomains']}</td></tr>
                    <tr><td>Wayback URLs</td><td>{summary['wayback_urls']}</td></tr>
                    <tr><td>Sensitive Files</td><td>{summary['sensitive_files']}</td></tr>
                    <tr><td>Juicy Info</td><td>{summary['juicy_info']}</td></tr>
                    <tr><td>Vulnerable URLs</td><td>{summary['vuln_urls']}</td></tr>
                    <tr><td>XSS Scan Files</td><td>{summary['xss_files']}</td></tr>
                    <tr><td>Directory Fuzzing</td><td>{summary['dir_fuzz']}</td></tr>
                    <tr><td>SQLMap Scans</td><td>{summary['sqlmap_scans']}</td></tr>
                    <tr><td>Nuclei Findings</td><td>{summary['nuclei_findings']}</td></tr>
                    <tr><td>Failed Steps</td><td>{summary['failures']}</td></tr>
                </tbody>
            </table>
        </div>
    """

    # Add detailed sections
    for section, content in file_contents.items():
        html_content += f"""
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-2 cursor-pointer" onclick="toggleSection('{section.lower().replace(' ', '_')}')">
                {section} ({summary.get(section.lower().replace(' ', '_'), 0)})
            </h3>
            <div id="{section.lower().replace(' ', '_')}" class="hidden">
                {'<pre class="bg-gray-100 dark:bg-gray-700 p-4 rounded">' + '<br>'.join(content) + '</pre>' if content else '<p>No data available.</p>'}
            </div>
        </div>
        """

    # XSS section
    html_content += """
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-2 cursor-pointer" onclick="toggleSection('xss')">XSS Scans ({})</h3>
            <div id="xss" class="hidden">
    """.format(summary['xss_files'])
    for filename, content in xss_contents:
        html_content += f"""
                <h4 class="font-medium mb-1">{html.escape(filename)}</h4>
                {'<pre class="bg-gray-100 dark:bg-gray-700 p-4 rounded">' + '<br>'.join(content) + '</pre>' if content else '<p>No data available.</p>'}
        """
    html_content += """
            </div>
        </div>
    """

    # SQLMap section
    html_content += """
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-2 cursor-pointer" onclick="toggleSection('sqlmap')">SQLMap Scans ({})</h3>
            <div id="sqlmap" class="hidden">
    """.format(summary['sqlmap_scans'])
    for log_dir, files in sqlmap_logs:
        html_content += f"""
                <h4 class="font-medium mb-1">{html.escape(log_dir)}</h4>
                {'<ul class="list-disc pl-5">' + ''.join(f'<li>{html.escape(f)}</li>' for f in files) + '</ul>' if files else '<p>No files generated.</p>'}
        """
    html_content += """
            </div>
        </div>
    """

    # Failures section
    if context.get('failures'):
        html_content += """
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mb-6">
            <h3 class="text-xl font-semibold mb-2 cursor-pointer text-red-600" onclick="toggleSection('failures')">Failed Steps ({})</h3>
            <div id="failures" class="hidden">
                <ul class="list-disc pl-5">
        """.format(summary['failures'])
        for step, error in context.get('failures', []):
            html_content += f"<li>{html.escape(step)}: {html.escape(error)}</li>"
        html_content += """
                </ul>
            </div>
        </div>
        """

    # Close HTML
    html_content += """
    </div>
</body>
</html>
    """

    # Save report
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        if console:
            console.print(color(f"[VENO] Report generated: {report_file}", 'green', bold=True))
        logger.info(f"Report generated: {report_file}")
    except Exception as e:
        if console:
            console.print(color(f"[VENO] Failed to save report: {e}", 'red', bold=True))
        with open(error_log, 'a', encoding='utf-8') as ferr:
            ferr.write(f"Failed to save report: {e}\n")
        logger.error(f"Failed to save report: {e}")

    elapsed = int(time.time() - start_time)
    logger.info(f"Report generation completed in {elapsed}s")
