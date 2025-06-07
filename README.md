# VENO - BUG HUNTING Tool

**VENO** automates reconnaissance and vulnerability discovery for bug bounty hunting. It collects subdomains, finds endpoints, and probes for issues like subdomain takeover, open directories, sensitive files, exposed parameters, and common web vulnerabilities using a range of open-source tools in a streamlined workflow.

---

## What VENO Does

- Discovers subdomains of a target domain
- Collects URLs and endpoints for further analysis
- Checks for potential subdomain takeover vulnerabilities
- Probes for open directories and hidden files
- Extracts sensitive information and JavaScript files
- Finds and analyzes GET/POST parameters
- Runs automated scans for:
  - Vulnerable endpoints (e.g., XSS, SQLi, SSRF, LFI/RFI, open redirects)
  - Exposed secrets and credentials
  - Misconfigured assets and services
  - Known CVEs and misconfigurations using templates
- Generates organized output and logs for each target

---

## Quick Start

```bash
git clone https://github.com/Veto95/VENO.git
cd VENO
chmod +x main.sh
./main.sh
```

Follow the interactive prompts to enter your target domains and select scan options.

---

## Community

- **Telegram:** [HELL SHELL](https://t.me/hacking_hell1)

---

## Author

- **VENO** by [0xCACT2S](https://github.com/Veto95)

---

## License

[MIT](LICENSE)
