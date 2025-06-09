---  

## VENO 🚀 — Automated Bug Hunting & Reconnaissance Suite   

**VENO** is a modular, command-line driven toolkit for bug bounty hunters, penetration testers, and security researchers. It automates reconnaissance and vulnerability assessment, fetching domains, sc[...]

---

## 💥 What VENO Does

- **Domain & Subdomain Discovery:** Collect targets from manual input, files, or external APIs. Cleans and validates domains.
- **Live Host Discovery:** Find active domains and subs.
- **URL & Endpoint Collection:** Gathers historical and active URLs, including dynamic params.
- **Secrets Extraction:** Pull API keys, tokens, and secrets from URLs and JavaScript.
- **Vulnerability Scanning:** XSS, SQLi, misconfig, and more—using top bug bounty tools.
- **Directory Fuzzing:** Probe for hidden dirs/files with custom or default wordlists.
- **WAF Detection:** Spots WAFs for bypass testing.
- **False Positive Filtering:** Validates and de-noises findings automatically.
- **Reporting:** Saves results, logs, and timestamps to `output/<domain>/`, including a **professional HTML dashboard**.
- **Customizable:** Choose scan intensity (`fast`, `normal`, `deep`), set thread count, enable/disable subdomain scan, select wordlists and more.

---

## ⚡ Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/Veto95/VENO.git
cd VENO
```

### 2. Install Requirements

- **Python**: 3.7+
- **System Tools**: See [`requirements_tools.md`](requirements_tools.md) for 3rd-party tools (auto-installer included)
- **OS**: Linux or WSL recommended  
- **Tested on:** Kali Linux, Parrot OS, Ubuntu

Install Python packages:

```bash
pip install -r requirements.txt
```

### 3. Global Setup (Recommended)

To make VENO globally available as `veno`:

```bash
python setup.py
```

- If `veno` is already global, it launches instantly.
- Otherwise, it sets up a global launcher (symlink/wrapper) so you can just type `veno` in any shell.

### 4. Launch the Shell

```bash
veno
# Or, if running locally:
python veno.py
```

You’ll get an nteractive prompt:

```
veno >
```

---

## 🕹 Usage Example

Command-driven shell, no wizards, no bullshit. Example session:

```
veno > set domain example.com
veno > set intensity deep
veno > set threads 20
veno > show options
veno > run
```

### Core Commands

- `set domain <target>` — Set target domain.
- `set intensity <fast|normal|deep>` — Choose scan mode.
- `set threads <number>` — Tune concurrency.
- `set wordlist <path>` — Custom wordlist for fuzzing.
- `set subscan <true|false>` — Enable/disable subdomain scan.
- `show options` — Show current config.
- `run` — Start the full scan pipeline.
- `help` — List all commands and options.
- `exit` / `quit` — Leave the shell.

---

## 📦 Output

All results, logs, and your sexy HTML report will appear in `output/<domain>/`.

---

## 🛠 System Tools

See [`requirements_tools.md`](requirements_tools.md) for a full list.  
**Don’t worry:** missing tools are auto-detected and the installer will guide you!

---

## 🤝 Community & Support

- **Telegram Channel:** [HELL SHELL](https://t.me/hacking_hell1)
- **Telegram Contact:** [0xCACT2S](https://t.me/CACT2S)
- **GitHub:** [github.com/Veto95/VENO](https://github.com/Veto95/VENO)

---

## 📝 License

MIT License

---

## ⚠️ Legal

**VENO is for authorized security testing and research only. Always get explicit permission before scanning any system.**

---

**Happy Hunting!** 🐱‍💻

---
