import sys
import time
import random

def banner():
    version = "1.0"
    hacker_phrases = [
        "Exploit", "Payload", "Zero-Day", "Pwn", "Hack", "Breach",
        "Shellcode", "Rootkit", "Backdoor", "Crack", "Fuzz", "Inject",
        "Phreak", "Skid", "Overload", "Bypass", "Sniff", "Dump"
    ]
    # Select 6 random phrases, ensure uniqueness
    selected_phrases = random.sample(hacker_phrases, 6)
    phrase_lines = [
        f"    [*] {selected_phrases[0]} the Void | {selected_phrases[1]} Unleashed | {selected_phrases[2]} Blitz",
        f"    [*] {selected_phrases[3]} Surge | {selected_phrases[4]} the Core | {selected_phrases[5]} Chaos"
    ]

    if sys.stdout.isatty():
        green = "\033[1;32m"
        purple = "\033[1;35m"
        cyan = "\033[1;36m"
        red = "\033[1;31m"
        reset = "\033[0m"
        delay = 0.03  # Typing effect delay per character
    else:
        green = purple = cyan = red = reset = ""
        delay = 0  # No delay for non-terminal output

    def type_effect(text):
        if delay:
            for char in text:
                print(char, end="", flush=True)
                time.sleep(delay)
            print()
        else:
            print(text)

    type_effect(f"{green}")
    type_effect(r"""
.-.   .-.,---.  .-. .-. .---.   
 \ \ / / | .-'  |  \| |/ .-. )  
  \ V /  | `-.  |   | || | |(_) 
   ) /   | .-'  | |\  || | | |  
  (_)    |  `--.| | |)|\ `-' /  
         /( __.'/(  (_) )---'   
        (__)   (__)    (_)     
    """)
    type_effect(f"{purple}          VENO v{version}")
    type_effect("     BUG HUNTING & RECON TOOL")
    type_effect(f"{reset}—-—-—-—-—-—-—-—-—-—-—-—-—-—-—")
    type_effect(f"{cyan}    Coder: 0xCACT2S")
    type_effect("    Telegram: HELL SHELL [https://t.me/hacking_hell1]")
    type_effect("    Contact: [https://t.me/CACT2S]")
    type_effect("    GitHub: https://github.com/Veto95/VENO")
    for line in phrase_lines:
        type_effect(f"{red}{line}")
    type_effect(f"{reset}")

if __name__ == "__main__":
    banner()
def get_banner_html():
    return """
<pre style="color:#1e90ff;font-weight:bold;font-family:monospace">
.-.   .-.,---.  .-. .-. .---.   
 \\ \\ / / | .-'  |  \\| |/ .-. )  
  \\ V /  | `-.  |   | || | |(_) 
   ) /   | .-'  | |\\  || | | |  
  (_)    |  `--.| | |)|\\ `-' /  
         /( __.'/(  (_) )---'   
        (__)   (__)    (_)     

             VENO v1.0
        BUG HUNTING & RECON TOOL

         coder: 0xCACT2S (Veto95)
 Telegram: HELL SHELL [https://t.me/hacking_hell1]
   GitHub: https://github.com/Veto95/VENO
</pre>
"""
