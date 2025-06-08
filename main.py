import sys
import logging
from modules.scanner import full_scan

def main():
    import argparse

    parser = argparse.ArgumentParser(description="VENO Automated Recon Scanner")
    parser.add_argument("domain", help="Target domain to scan (e.g. example.com)")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("--no-subdomains", action="store_true", help="Skip subdomain scan")
    parser.add_argument("--threads", type=int, default=5, help="Threads for applicable tools")
    parser.add_argument("--wordlist", default="", help="Custom wordlist for fuzzing/discovery")
    parser.add_argument("--banner-html", default="", help="Custom HTML banner for report")

    args = parser.parse_args()

    config = {
        "output_dir": args.output,
        "subdomains": not args.no_subdomains,
        "banner_html": args.banner_html,
        "scan_config": {
            "threads": args.threads,
        },
        "wordlist": args.wordlist,
    }

    logging.basicConfig(
        filename=f"{args.output}/{args.domain}/veno.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    print(f"\033[1;35m[VENO]\033[0m Starting full scan for \033[1;36m{args.domain}\033[0m")
    try:
        full_scan(args.domain, config)
        print(f"\033[1;32m[VENO]\033[0m Scan completed for \033[1;36m{args.domain}\033[0m")
    except KeyboardInterrupt:
        print(f"\033[1;31m[VENO]\033[0m Scan interrupted by user!")
        sys.exit(1)
    except Exception as e:
        print(f"\033[1;31m[VENO]\033[0m Fatal error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
