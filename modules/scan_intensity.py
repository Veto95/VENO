def get_scan_intensity(outdir):
    print("Enter scan intensity configuration:")
    try:
        threads = int(input("Threads [default 10]: ") or "10")
    except Exception:
        threads = 10
    try:
        hak_depth = int(input("Hakrawler depth [default 2]: ") or "2")
    except Exception:
        hak_depth = 2
    sqlmap_flags = input("SQLMap flags (optional): ").strip()
    try:
        recursion_depth = int(input("Recursion depth [default 1]: ") or "1")
    except Exception:
        recursion_depth = 1
    return {
        "threads": threads,
        "hak_depth": hak_depth,
        "sqlmap_flags": sqlmap_flags,
        "recursion_depth": recursion_depth
    }
