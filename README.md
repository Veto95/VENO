# VENO - Automated Bug Hunting & Reconnaissance Suite

**VENO** is your all-in-one toolkit for bug bounty hunters, penetration testers, and security researchers.  
It automates reconnaissance, vulnerability assessment, and reporting—so you can focus on finding real bugs.

---

## Features

- **Domain Reconnaissance:** Input domains manually or via file, with built-in validation.
- **Scan Intensity Selection:** Choose between Fast, Normal, or Deep (WAF-evasive) scan modes.
- **Automatic Tool Chaining:** VENO selects and orchestrates all tools based on your scan intensity—no manual tool selection needed.
- **Subdomain Discovery:** Optionally include subdomain enumeration.
- **Dynamic Parameter & Endpoint Discovery:** Finds endpoints/parameters, analyzes them, and targets them for deeper testing.
- **Sensitive Data Exposure Detection:** Extracts and validates potentially exposed files and credentials.
- **Juicy Info & Secrets Finder:** Scans for API keys, tokens, and secrets in URLs and JavaScript files, with live validation.
- **Vulnerability Scanning:** Integrated XSS, SQLi, and misconfiguration checks using modern techniques and payloads.
- **False Positive Filtering:** Filters and validates findings, surfacing only actionable results.
- **Comprehensive Reporting:**  
  - **Interactive HTML Report:** Professionally styled with collapsible table of contents, VENO banner, and raw outputs.
  - **Markdown & PDF Summaries:** For easy sharing or submission.
- **Easy to Use:** Modular, colorized CLI with clear progress and error reporting.
- **Extensible:** Easily add new tools and features.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Veto95/VENO.git
cd VENO
```

### 2. Install Requirements

- **Python:** 3.7 or newer.
- **System Tools:** Install all required bug bounty/recon tools.  
  See [`requirements_tools.md`](requirements_tools.md) for the full list.
- **Python Packages:**
  ```bash
  pip install -r requirements.txt
  ```

> **Tip:** For best compatibility, use Linux or WSL.

### 3. Run VENO

```bash
python main.py
```

### 4. Follow the Prompts

- Enter your target domains (manual input or file).
- Select scan intensity (Fast, Normal, Deep).
- Choose your wordlist.
- (Optionally) enable subdomain scan.

VENO will automatically select the right tools, validate findings, and generate advanced reports.

### 5. Review Your Results

- All results are stored in the `output/` directory.
- You will find per-domain interactive HTML reports (with the VENO banner), PDFs, summaries, and raw tool outputs.

---

## Community & Support

- **Telegram Channel:** [HELL SHELL](https://t.me/hacking_hell1)
- **Telegram (Contact):** [0xCACT2S](https://t.me/CACT2S)

---

## License

This project is licensed under the [MIT License](LICENSE.md).

---

## Legal

**VENO is for authorized security testing and research purposes only.**  
Always obtain proper authorization before scanning any system.

---

**Happy Hunting!**
