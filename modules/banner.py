import sys
import time
import random

def banner():
    version = "1.0"
    phrases = [
        "Recon", "Scope", "Vulnerability", "Exploit", "Payload", "XSS",
        "SQLi", "LFI", "RCE", "SSRF", "Bypass", "Enumeration", "Fuzz",
        "Disclosure", "Reward", "Bounty", "Hacker", "Report", "Payout",
        "PoC", "Chain", "Critical", "Zero-Day", "Automation", "Triager",
        "Hall of Fame", "Subdomain", "Takeover", "Responsible", "Ethical",
        "Duplicate", "Out of Scope", "Race Condition"
    ]
    selected_phrases = random.sample(phrases, 6)
    phrase_lines = [
        f"    [*] {selected_phrases[0]} the Target | {selected_phrases[1]} Exposed | {selected_phrases[2]} Blitz",
        f"    [*] {selected_phrases[3]} Surge | {selected_phrases[4]} Recon | {selected_phrases[5]} Reward"
    ]

    if sys.stdout.isatty():
        green = "\033[1;32m"
        purple = "\033[1;35m"
        cyan = "\033[1;36m"
        red = "\033[1;31m"
        reset = "\033[0m"
        delay = 0.005
    else:
        green = purple = cyan = red = reset = ""
        delay = 0

    def type_effect(text):
        if delay:
            for char in text:
                print(char, end="", flush=True)
                time.sleep(delay)
            print()
        else:
            print(text)

    type_effect(f"{green}")
    print(r"""
 .-.   .-.,---.  .-. .-. .---.   
  \ \ / / | .-'  |  \| |/ .-. )  
   \ V /  | `-.  |   | || | |(_) 
    ) /   | .-'  | |\  || | | |  
   (_)    |  `--.| | | |\ `-' /  
          /( __.'/(  (_) )---'   
         (__)   (__)    (_)     
    """)
    print(f"{purple}          VENO v{version}")
    print("     BUG BOUNTY & RECON TOOL")
    type_effect(f"{reset}—-—-—-—-—-—-—-—-—-—-—-—-—-—-—--")
    type_effect(f"{cyan}    Coder: 0xCACT2S")
    print("    Telegram: HELL SHELL https://t.me/H3LL_SH3LL")
    print("    Contact: https://t.me/CACT2S")
    print("    GitHub: https://github.com/Veto95/VENO")
    for line in phrase_lines:
        type_effect(f"{red}{line}")
    type_effect(f"{reset}")

def get_banner_html():
    return r"""
<pre style="color:#1e90ff;font-weight:bold;font-family:monospace">
 .-.   .-.,---.  .-. .-. .---.   
  \ \ / / | .-'  |  \| |/ .-. )  
   \ V /  | `-.  |   | || | |(_) 
    ) /   | .-'  | |\  || | | |  
   (_)    |  `--.| | | |\ `-' /  
          /( __.'/(  (_) )---'   
         (__)   (__)    (_)     

    VENO v1.0
    BUG BOUNTY & RECON TOOL
    Coder: 0xCACT2S
    Telegram: HELL SHELL [https://t.me/H3LL_SH3LL]
    Contact: [https://t.me/CACT2S]
    GitHub: https://github.com/Veto95/VENO
    [Bug bounty flavor lines here!]
</pre>
"""
