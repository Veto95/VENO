import logging
from modules.scanner_steps import scanner_steps

try:
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    from rich.console import Console
    console = Console()
except ImportError:
    Progress = None
    console = None

# Optional meme module -- import if it exists
try:
    from modules.memes import get_ascii_meme, get_insult
    HAS_MEMES = True
except ImportError:
    HAS_MEMES = False

def print_status(msg, color="cyan"):
    if console:
        console.print(f"[{color}][VENO][/]{msg}")
    else:
        print(f"[VENO] {msg}")

def full_scan(domain, config):
    """
    Executes a full scan using the ordered scanner_steps list.
    Each step receives (domain, config, context), and can update context with findings.
    Output is minimal: just what step is running, no tool output.
    Returns context, and a list of failed steps for UX summary.
    """
    logging.info(f"[VENO] Starting full scan for {domain}")
    context = {}
    failures = []

    def step_nice(step):
        return step.__name__.replace("step_", "").replace("_", " ").title()

    # Print a pre-scan meme for maximum morale
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
                progress.console.print(f"[magenta]> {step_name}...[/magenta]")
                try:
                    step(domain, config, context)
                except Exception as e:
                    msg = f"[ERROR] Step '{step_name}' failed: {e}"
                    progress.console.print(f"[red]{msg}[/red]")
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
                print_status(msg, "red")
                logging.error(msg)
                failures.append((step_name, str(e)))

    if failures:
        print_status(f"{len(failures)} scan steps failed:", "red")
        for step, err in failures:
            print_status(f"  {step}: {err}", "red")
    else:
        print_status("All scan steps completed successfully!", "green")

    # End-of-scan meme/insult
    if HAS_MEMES:
        print_status(get_insult(), "magenta")
        print_status(get_ascii_meme(), "green")

    logging.info(f"[VENO] Full scan completed for {domain}")
    context["failures"] = failures
    return context
