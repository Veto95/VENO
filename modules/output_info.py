import os

def notify_output_location(domain, outdir):
    """
    Inform the user about the output directory for the current scan.
    """
    domain_dir = os.path.join(outdir, domain)
    print(f"\n[VENO] All findings, logs, and reports for {domain} are saved in:\n    {domain_dir}\n")
    print("[VENO] You will find:")
    print("  - Interactive HTML reports")
    print("  - Markdown/PDF summaries")
    print("  - Raw outputs and logs")
