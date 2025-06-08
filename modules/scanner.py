import logging
from modules.scanner_steps import scanner_steps

try:
    from rich.progress import Progress
except ImportError:
    Progress = None

def full_scan(domain, config):
    """
    Executes a full scan using the ordered scanner_steps list.
    Each step receives (domain, config, context), and can update context with findings.
    """
    logging.info(f"[VENO] Starting full scan for {domain}")
    context = {}

    if Progress:
        with Progress() as progress:
            task = progress.add_task(f"[yellow]Scanning {domain}", total=len(scanner_steps))
            for step in scanner_steps:
                step_name = step.__name__
                progress.console.print(f"[magenta]{step_name}[/magenta]")
                try:
                    step(domain, config, context)
                except Exception as e:
                    logging.error(f"Step {step_name} failed for {domain}: {e}")
                progress.update(task, advance=1)
    else:
        for step in scanner_steps:
            step_name = step.__name__
            print(f"[VENO] {step_name}")
            try:
                step(domain, config, context)
            except Exception as e:
                logging.error(f"Step {step_name} failed for {domain}: {e}")

    logging.info(f"[VENO] Full scan completed for {domain}")
    return context
