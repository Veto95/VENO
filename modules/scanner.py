import os
import logging
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

def run_scanner(domain, config_overrides=None, context=None):
    """
    Run a VENO scan on a domain with optional config overrides.
    :param domain: Target domain, e.g. 'example.com'
    :param config_overrides: dict of config overrides (e.g., {'intensity': 'heavy', 'output_dir': '/tmp/x'})
    :param context: optional dict for scan context (default: new dict)
    """
    if config_overrides is None:
        config_overrides = {}
    if context is None:
        context = {}

    intensity = config_overrides.get("intensity", "medium")
    if intensity not in SCAN_INTENSITIES:
        raise ValueError(
            f"Unknown intensity profile: {intensity} (options: {list(SCAN_INTENSITIES.keys())})"
        )
    profile = SCAN_INTENSITIES[intensity]
    config = dict(profile)  # Copy to allow override

    # Apply overrides from the caller/main
    config["output_dir"] = config_overrides.get("output_dir", DEFAULT_OUTPUT_DIR)
    config["intensity"] = intensity
    if "wordlist" in config_overrides:
        config["wordlist"] = config_overrides["wordlist"]
    if "threads" in config_overrides:
        config["threads"] = config_overrides["threads"]
    if "subscan" in config_overrides:
        config["subscan"] = config_overrides["subscan"]

    print(f"\n[VENO] Target: {domain}")
    print(f"[VENO] Intensity profile: {intensity} — {profile.get('description', '')}")
    print(f"[VENO] Output dir: {config['output_dir']}")
    print(f"[VENO] Wordlist: {config['wordlist']}")
    print(f"[VENO] Threads: {config['threads']}\n")

    os.makedirs(config["output_dir"], exist_ok=True)

    print_status(f"[VENO] Starting scan for: {domain}", "yellow")
    print_status(f" - Output directory: {config['output_dir']}", "magenta")
    print_status(f" - Wordlist: {config['wordlist']}", "cyan")
    print_status(f" - Threads: {config['threads']}", "blue")
    print_status(f" - Subdomain scan: {'enabled' if config.get('subscan', True) else 'disabled'}", "green")
    print_status(f" - Intensity: {intensity}", "yellow")
    print_status("-" * 65, "magenta")

    logging.info(f"[VENO] Starting scan for {domain}")

    failures = []

    def step_nice(step):
        return step.__name__.replace("step_", "").replace("_", " ").title()

    if HAS_MEMES:
        print_status(get_ascii_meme(), "yellow")

    scanner_steps = get_steps_for_intensity(intensity)
    total_steps = len(scanner_steps)

    if Progress:
        with Progress(
            TextColumn("[bold cyan]VENO[/bold cyan]", justify="right"),
            BarColumn(),
            TextColumn("{task.description}"),
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
        for step in scanner_steps:
            step_name = step_nice(step)
            print_status(f"> {step_name}...", "magenta")
            try:
                step(domain, config, context)
            except Exception as e:
                msg = f"[ERROR] Step '{step_name}' failed: {e}"
                print_error(msg)
                logging.error(msg)
                failures.append((step_name, str(e)))

    if failures:
        print_error(f"{len(failures)} scan steps failed:")
        for step, err in failures:
            print_error(f"  {step}: {err}")
    else:
        print_success("All scan steps completed successfully!")

    if HAS_MEMES:
        print_status(get_insult(), "magenta")
        print_status(get_ascii_meme(), "green")

    logging.info(f"[VENO] Scan complete for {domain}")
    context["failures"] = failures
    return context
