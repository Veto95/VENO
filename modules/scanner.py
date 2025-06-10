import os
import logging
import time
from modules.scanner_steps import run_scan, get_steps_for_intensity
from modules.scan_intensity import SCAN_INTENSITIES, DEFAULT_OUTPUT_DIR

try:
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.console import Console
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    Progress = None
    RICH_AVAILABLE = False
    console = None

try:
    from modules.memes import get_ascii_meme, get_insult
    HAS_MEMES = True
except ImportError:
    HAS_MEMES = False
    get_ascii_meme = lambda: "¯\\_(ツ)_/¯"
    get_insult = lambda: "No memes for you!"

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

def print_status(msg, colorname="cyan", bold=True):
    if console:
        console.print(color(msg, colorname, bold=bold))
    else:
        print(color(msg, colorname, bold=bold))

def print_error(msg):
    if console:
        console.print(color(msg, "red", bold=True, bg="black"))
    else:
        print(color(msg, "red", bold=True, bg="black"))

def print_success(msg):
    if console:
        console.print(color(msg, "green", bold=True))
    else:
        print(color(msg, "green", bold=True))

def validate_config(config, domain):
    """Validate configuration settings."""
    required_keys = ['intensity', 'output_dir', 'threads', 'wordlist', 'subscan']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required config keys: {', '.join(missing_keys)}")
    
    # Resolve output_dir to absolute path
    output_dir = os.path.abspath(config['output_dir'])
    config['output_dir'] = output_dir  # Update config with absolute path
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        raise ValueError(f"Cannot create output directory: {output_dir} ({e})")
    
    if config['wordlist'] and not os.path.isfile(config['wordlist']):
        raise ValueError(f"Wordlist file not found: {config['wordlist']}")
    
    if config['intensity'] not in SCAN_INTENSITIES:
        raise ValueError(
            f"Unknown intensity profile: {config['intensity']} (options: {list(SCAN_INTENSITIES.keys())})"
        )

def run_scanner(domain, config_overrides=None, context=None):
    """
    Run a VENO scan on a domain with optional config overrides.
    :param domain: Target domain, e.g. 'example.com'
    :param config_overrides: dict of config overrides (e.g., {'intensity': 'heavy', 'output_dir': '/tmp/x'})
    :param context: optional dict for scan context (default: new dict)
    """
    start_time = time.time()
    logging.info(f"[VENO] Scan started for {domain} at {time.ctime(start_time)}")
    
    if config_overrides is None:
        config_overrides = {}
    if context is None:
        context = {}

    # Initialize config with defaults from intensity profile
    intensity = config_overrides.get("intensity", "medium")
    profile = SCAN_INTENSITIES.get(intensity, {})
    config = dict(profile)  # Copy to allow overrides

    # Apply overrides
    config["output_dir"] = config_overrides.get("output_dir", DEFAULT_OUTPUT_DIR)
    config["intensity"] = intensity
    config["threads"] = config_overrides.get("threads", profile.get("threads", 5))
    config["wordlist"] = config_overrides.get("wordlist", profile.get("wordlist", ""))
    config["subscan"] = config_overrides.get("subscan", profile.get("subscan", True))

    try:
        validate_config(config, domain)
    except ValueError as e:
        print_error(f"[VENO] Configuration error: {e}")
        logging.error(f"[VENO] Configuration error: {e}")
        return context

    # Display minimal scan start message
    print_status(f"\n[VENO] Starting scan for: {domain}", "yellow")
    print_status("-" * 65, "magenta")

    if HAS_MEMES:
        print_status(get_ascii_meme(), "yellow")

    scanner_steps = get_steps_for_intensity(intensity)
    total_steps = len(scanner_steps)
    failures = []

    def step_nice(step):
        return step.__name__.replace("step_", "").replace("_", " ").title()

    if Progress:
        with Progress(
            TextColumn("[bold cyan]VENO[/bold cyan]", justify="right"),
            BarColumn(bar_width=None),
            TextColumn("{task.description} ({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"[white]Scanning {domain}[/white]", total=total_steps)
            for step in scanner_steps:
                step_name = step_nice(step)
                progress.console.print(color(f"> {step_name}...", "magenta"))
                try:
                    step(domain, config, context)
                except Exception as e:
                    msg = f"[ERROR] Step '{step_name}' failed: {e}"
                    progress.console.print(color(msg, "red"))
                    logging.error(msg)
                    failures.append((step_name, str(e)))
                progress.update(task, advance=1)
    else:
        for i, step in enumerate(scanner_steps, 1):
            step_name = step_nice(step)
            print_status(f"> {step_name} ({i}/{total_steps})...", "magenta")
            try:
                step(domain, config, context)
            except Exception as e:
                msg = f"[ERROR] Step '{step_name}' failed: {e}"
                print_error(msg)
                logging.error(msg)
                failures.append((step_name, str(e)))

    # Scan completion summary
    elapsed = int(time.time() - start_time)
    if failures:
        print_error(f"[VENO] Scan completed with {len(failures)} failed steps in {elapsed}s:")
        for step, err in failures:
            print_error(f"  {step}: {err}")
    else:
        print_success(f"[VENO] Scan completed successfully in {elapsed}s with no failures!")

    if HAS_MEMES:
        print_status(get_insult(), "magenta")
        print_status(get_ascii_meme(), "green")

    logging.info(f"[VENO] Scan completed for {domain} at {time.ctime(time.time())}")
    context["failures"] = failures
    return context
