# VENO 🚀 — Automated Bug Hunting & Reconnaissance Suite

**VENO** is the ultimate all-in-one toolkit for bug bounty hunters, penetration testers, and security researchers.  
It supercharges your workflow by automating reconnaissance, vulnerability assessment, and reporting—so you can focus on hacking, not hassle.

---

## 💥 Features

- **Domain Reconnaissance:** Input domains manually or via file, with robust validation.
- **Scan Intensity Modes:** Fast, Normal, or Deep (WAF-evasive) scanning—tailor depth to your target.
- **Automatic Tool Chaining:** VENO intelligently selects and orchestrates the best tools for each scan.
- **Subdomain Enumeration:** Optionally uncover hidden subdomains for a wider attack surface.
- **Dynamic Parameter & Endpoint Discovery:** Finds and probes endpoints for deeper, juicier bugs.
- **Sensitive Data Exposure Detection:** Extracts and validates potentially exposed files and credentials.
- **Secrets Finder:** Scans for API keys, tokens, and secrets in URLs and JavaScript with live validation.
- **Vulnerability Scanning:** Integrated XSS, SQLi, and misconfiguration checks using modern payloads.
- **False Positive Filtering:** Aggressively validates findings, so you only see what actually matters.
- **Comprehensive Reporting:**  
  - **Interactive HTML Reports:** Professional, hacker-styled, with a collapsible TOC and flashy VENO banner.
  - **Markdown & PDF Summaries:** Perfect for sharing or submitting your findings.
- **Modular CLI:** Colorized, with clear progress, error reporting, and easy extensibility.

---

## ⚡ Getting Started

### 1. Clone the Repo

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

> **Pro Tip:** For best compatibility, use Linux or WSL (Windows Subsystem for Linux).

### 3. Run VENO

```bash
python main.py
```

### 4. Interactive Wizard

- Choose how to input your target domains (manual or file).
- Select scan intensity (Fast, Normal, Deep).
- Pick your wordlist.
- Optionally enable subdomain scanning.

VENO will handle tool selection, scan orchestration, validation, and sexy report generation—automagically.

### 5. Results

- All outputs are stored in the `output/` directory.
- Find per-domain interactive HTML reports (with the VENO banner), PDFs, summaries, and raw tool results.

---

## 🤝 Community & Support

- **Telegram Channel:** [HELL SHELL](https://t.me/hacking_hell1)
- **Telegram (Contact):** [0xCACT2S](https://t.me/CACT2S)

---

## 📝 License

This project is licensed under the [MIT License](LICENSE.md).

---

## ⚠️ Legal

**VENO is for authorized security testing and research purposes only.**  
Always obtain proper authorization before scanning any system.

---

**Happy Hunting!** 🐱‍💻
