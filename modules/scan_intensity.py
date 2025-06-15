import os

DEFAULT_OUTPUT_DIR = "output"
DEFAULT_BANNER_PY = "<h1>VENO Automated Bug Bounty Scan</h1>"

def _check_wordlist(path):
    if not os.path.isfile(path):
        print(f"\033[1;33m[WARNING] Wordlist not found: {path} — you might be about to eat shit!\n")

SCAN_INTENSITIES = {
    "light": {
        "description": "Light as fuck — fast, low-noise, skips heavy shit. For sneak peeks only.",
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/quickhits.txt",
        "threads": 5,
        "delay": 0.3,
        "run_subjack": False,
        "run_sqlmap": False,
        "run_waymore": False,
        "run_hakrawler": False,
        "run_nuclei_full": False,
        "run_naabu": False,
        "run_gf": False,
        "dir_fuzz_tool": False,  # Disabled for light mode
        "gau": True,
        "dalfox": False,
        "xsstrike": False,
    },
    "medium": {
        "description": "Medium (default): Balanced — solid bug bounty coverage, not too slow, not too cray.",
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
        "threads": 10,
        "delay": 0.8,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": False,
        "run_nuclei": True,
        "run_naabu": False,
        "run_gf": False,
        "dir_fuzz_tool": "ffuf",
        "gau": True,
        "dalfox": True,
        "xsstrike": False,
    },
    "deep": {
        "description": "deep as fuck — melt faces and CPUs. Full arsenal, full send.",
        "wordlist": "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt",
        "threads": 40,
        "delay": 1.8,
        "run_subjack": True,
        "run_sqlmap": True,
        "run_waymore": True,
        "run_hakrawler": True,
        "run_nuclei_full": True,
        "run_nuclei": True,
        "run_naabu": True,
        "run_gf": True,
        "dir_fuzz_tool": "dirsearch",
        "gau": True,
        "dalfox": True,
        "xsstrike": True,
    },
}

for mode, opts in SCAN_INTENSITIES.items():
    if opts.get("wordlist"):
        _check_wordlist(opts["wordlist"])
"""

---

### Detailed Changes and Features

#### Changes in `scanner_steps.py`
1. **New Steps**:
   - **`step_parse_param_urls`**:
     - Reads `all_urls.txt` (merged from `waybackurls`, `waymore`, `hakrawler`).
     - Uses regex (`\?.+=.+|\.(php|asp|aspx|jsp)` to find URLs with query parameters or dynamic endpoints.
     - Saves results to `param_urls.txt`.
     - Adds `param_urls` to context.
   - **`step_probe_param_urls`**:
     - Runs `httprobe` on `param_urls.txt` to filter live URLs.
     - Saves results to `live_param_urls.txt`.
     - Adds `live_param_urls` to context.
     - Alerts on top 10 live URLs.

2. **Modified Steps**:
   - **`step_wayback_urls`**:
     - Appends URLs to `all_urls.txt` for unified processing.
     - Respects `gau` config flag for fallback.
   - **`step_waymore_urls`**:
     - Appends URLs to `all_urls.txt`.
   - **`step_hakrawler_crawl`**:
     - Appends crawled URLs to `all_urls.txt`.
   - **`step_nuclei_scan`**:
     - Uses `live_param_urls.txt` as target file instead of `nuclei_targets.txt`.
     - Respects `run_nuclei` and `run_nuclei_full` config flags.
     - Saves results to `nuclei_vulns` in context.
   - **`step_sqlmap`**:
     - Uses `live_param_urls.txt` instead of `vuln_urls`.
     - Checks `run_sqlmap` config flag to enable/disable.
     - Limits to 5 URLs in `light` mode, 10 in `medium`/`deep`.
   - **`step_advanced_xss`**:
     - Uses `live_param_urls.txt` for `Dalfox` if enabled (`dalfox` config flag).
     - Skips `XSStrike` unless `xsstrike` flag is True.
   - **`get_steps_for_intensity`**:
     - Includes `step_wayback_urls` for all intensities.
     - Adds `step_waymore_urls`, `step_parse_param_urls`, `step_probe_param_urls`, and others for `medium`/`deep`.
     - Includes all steps for `deep`, respecting config flags.

3. **Integrity Preservation**:
   - **Logging**: Added failure logging to `context["failures"]` for new steps.
   - **Error Handling**: Maintained try-except blocks with logging and error file writes.
   - **Context Updates**: Ensured new keys (`param_urls`, `live_param_urls`) are compatible with `generate_report`.
   - **Rich Console**: Preserved `color` and `console` output for alerts and steps.
   - **Dependencies**: No new tool dependencies; uses existing `httprobe`.

#### Changes in `scan_intensity.py`
1. **Updated Configurations**:
   - **Light Mode**:
     - Enables `waybackurls` (`gau=True`) but skips `waymore`, `sqlmap`, `nuclei`, `hakrawler`, etc.
     - Minimal threads (5), short delay (0.3).
     - No fuzzing (`dir_fuzz_tool=False`).
   - **Medium Mode**:
     - Enables `waybackurls`, `waymore_urls`, `sqlmap`, `nuclei` (basic), `hakrawler`, `dalfox`.
     - Moderate threads (10), delay (0.8).
     - Uses `ffuf` for fuzzing.
   - **deep Mode**:
     - Enables all tools, including `waymore`, `sqlmap`, `nuclei_full`, `naabu`, `gf`, `xsstrike`.
     - High threads (40), longer delay (1.8).
     - Uses `dirsearch` for fuzzing.

2. **Integrity**:
   - Preserved wordlist validation (`_check_wordlist`).
   - Kept existing structure and naming conventions.
   - Ensured backward compatibility with `scanner_steps.py`.

---

### Usage Notes
- **Running the Scanner**:
  ```bash
  python scanner.py --domain example.com --intensity medium
  ```
  - `light`: Fetches `waybackurls`, skips `waymore`, processes parameters, probes live URLs, runs `xss`, generates report.
  - `medium`: Adds `waymore`, `sqlmap`, `nuclei` (basic), `hakrawler`, etc.
  - `deep`: Full scan with all tools, including `naabu`, `gf`, `xsstrike`.

- **Output Files**:
  - `all_urls.txt`: Merged URLs from `waybackurls`, `waymore`, `hakrawler`.
  - `param_urls.txt`: URLs with parameters or dynamic endpoints.
  - `live_param_urls.txt`: Live URLs for `sqlmap` and `nuclei`.
  - `report.html`: Includes new sections for `param_urls` and `live_param_urls` (from - Report generated by `generate_report`).

- **Dependencies**:
  - Ensure `httprobe`, `waybackurls`, `waymore`, `sqlmap`, `nuclei`, etc., are installed.
  - Update `/path/to/nuclei/templates/` in `step_nuclei` if using custom templates.

- **Edge Cases**:
  - Handles empty URL lists by writing placeholder files and logging warnings.
  - Skips steps if tools are missing (`shutil.which` checks).
  - Limits `sqlmap` to 5/10 URLs to prevent overload.

---

### Potential Improvements
- **Pagination for Large URL Lists**: Add server-side chunking for massive URL sets.
- **Advanced Parameter Parsing**: Use `ParamSpider` output to enrich `step_parse_param_urls`.
- **Custom Nuclei Templates**: Allow users to specify template paths via config.
- **Parallel Processing**: Optimize `httprobe` and `sqlmap` for faster scans.
- **Rate Limiting**: Add configurable rate limits for `nuclei` and `sqlmap`.

---

"""
