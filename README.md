# VENO 🚀 — Automated Bug Hunting & Reconnaissance Suite

**VENO** is a modular, command-line driven toolkit for bug bounty hunters, penetration testers, and security researchers. It automates reconnaissance and vulnerability assessment, fetching domains, subdomains, URLs, and vulnerabilities, with robust filtering and professional reporting—all controlled from a colorful interactive shell.

---

## 💥 What VENO Fetches and Does

- **Fetches Domains/Subdomains**: Collects domains from manual input, files, or external sources, validating them for accuracy.
- **Cleans and Validates Domains**: Removes protocols, paths, and wildcards (e.g., `https://*.example.com` → `example.com`).
- **Fetches Live Hosts**: Identifies active domains and subdomains.
- **Fetches URLs and Endpoints**: Gathers historical and active URLs, including dynamic parameters.
- **Fetches Secrets**: Extracts API keys, tokens, and secrets from URLs and JavaScript files.
- **Scans for Vulnerabilities**: Detects XSS, SQL injection, misconfigurations, and more.
- **Performs Directory Fuzzing**: Probes for hidden directories and files using custom or default wordlists.
- **Checks WAF Protection**: Identifies WAF-protected domains for potential bypass testing.
- **Filters False Positives**: Validates findings to reduce noise.
- **Generates Reports**: Saves results, logs, and timestamps to `output/<domain>/`, including a professional HTML report.
- **Customizes Scans**: Configures scan intensity (`fast`, `normal`, `deep`), thread concurrency, and subdomain scanning.

---

## ⚡ Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Veto95/VENO.git
cd VENO
```

### 2. Install Requirements

- **Python**: 3.7+
- **System Tools**: See [`requirements_tools.md`](requirements_tools.md)
- **OS**: Linux or WSL recommended
- **Tested distro**:kali linux,parrot os and ubuntu

Install Python packages:

```bash
pip install -r requirements.txt
```

### 3. Launch the Shell

```bash
python veno.py
```

You’ll get a colored interactive prompt:

```
veno >
```

---

## 🕹 Usage Example

Control everything with shell commands—no step-by-step wizard. Example session:

```
veno > set domain example.com
veno > set intensity deep
veno > set threads 20
veno > show options
veno > run
```

### Commands

- `set domain <target>`: Set target domain.
- `set intensity <fast|normal|deep>`: Choose scan mode.
- `set threads <number>`: Control concurrency.
- `set wordlist <path>`: Custom wordlist for fuzzing.
- `set subscan <true|false>`: Enable/disable subdomain scan.
- `show options`: Show current config.
- `run`: Start the full scan pipeline.
- `help`: List all commands and options.

---

## 📦 Output

Results, logs, and HTML report in `output/<domain>/`.

---

## 🛠 System Tools

See [`requirements_tools.md`](requirements_tools.md) for required tools.

---

## 🤝 Community & Support

- **Telegram Channel:** [HELL SHELL](https://t.me/hacking_hell1)
- **Telegram Contact:** [0xCACT2S](https://t.me/CACT2S)

---

## 📝 License

MIT License

---

## ⚠️ Legal

**VENO is for authorized security testing and research only. Always get explicit permission before scanning any system.**

---

**Happy Hunting!** 🐱‍💻
```
