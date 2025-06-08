def print_scan_start(domain):
    print(f"\n[VENO] Starting scan for: {domain}")

def print_tool_info(tools):
    print(f"[VENO] Auto-selected tools for this scan: {', '.join(tools)}")

def print_step(msg):
    print(f"[VENO] {msg}")

def print_completion(domain):
    print(f"[VENO] Scan completed for: {domain}")
