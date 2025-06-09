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
    Output is minimal: just what step is running, no tool noise.
    """
    logging.info(f"[VENO] Starting full scan for {domain}")
    context = {}

    if Progress:
        with Progress() as progress:
            task = progress.add_task(f"[yellow]Scanning {domain}", total=len(scanner_steps))
            for step in scanner_steps:
                step_name = step.__name__
                # Only print the step name, no tool output
                progress.console.print(f"[cyan][VENO][/cyan] {step_name.replace('step_', '').replace('_', ' ').title()}")
                try:
                    step(domain, config, context)
                except Exception as e:
                    progress.console.print(f"[red][ERROR][/red] Step {step_name} failed: {e}")
                    logging.error(f"Step {step_name} failed for {domain}: {e}")
                progress.update(task, advance=1)
    else:
        for step in scanner_steps:
            step_name = step.__name__
            print(f"[VENO] {step_name.replace('step_', '').replace('_', ' ').title()}")
            try:
                step(domain, config, context)
            except Exception as e:
                print(f"[ERROR] Step {step_name} failed: {e}")
                logging.error(f"Step {step_name} failed for {domain}: {e}")

    logging.info(f"[VENO] Full scan completed for {domain}")
    return context
