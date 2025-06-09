import logging
from modules.scanner_steps import scanner_steps

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

def full_scan(config):
    """
    Aligned with veno.py: expects a single config dict!
    Executes scanner_steps. All output is colorized.
    """
    domain = config.get("domain", "")
    output_dir = config.get("output_dir", "output")
    wordlist = config.get("wordlist", "")
    threads = config.get("scan_config", {}).get("threads", 20)
    subscan = config.get("subscan", True)
    intensity = config.get("intensity", "normal")

    if not domain:
        print_error("[VENO] Domain not set. Aborting scan.")
        return

    print_status(f"[VENO] Starting scan for: {domain}", "yellow")
    print_status(f" - Output directory: {output_dir}", "magenta")
    print_status(f" - Wordlist: {wordlist}", "cyan")
    print_status(f" - Threads: {threads}", "blue")
    print_status(f" - Subdomain scan: {'enabled' if subscan else 'disabled'}", "green")
    print_status(f" - Intensity: {intensity}", "yellow")
    print_status("-" * 65, "magenta")

    logging.info(f"[VENO] Starting full scan for {domain}")
    context = {}
    failures = []

    def step_nice(step):
        return step.__name__.replace("step_", "").replace("_", " ").title()

    # Pre-scan meme
    if HAS_MEMES:
        print_status(get_ascii_meme(), "yellow")

    if Progress:
        with Progress(
            TextColumn("[bold cyan]VENO[/bold cyan]", justify="right"),
            BarColumn(),
            TextColumn("{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"[white]Scanning {domain}[/white]", total=len(scanner_steps))
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

    # End-of-scan meme/insult
    if HAS_MEMES:
        print_status(get_insult(), "magenta")
        print_status(get_ascii_meme(), "green")

    logging.info(f"[VENO] Full scan completed for {domain}")
    context["failures"] = failures
    return context
