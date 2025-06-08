import os

def get_wordlist():
    default_wordlist = "/usr/share/dirb/wordlists/common.txt"
    print("\n[VENO] WORDLIST SELECTION")
    while True:
        use_default = input(
            f"Would you like to use the default wordlist? [{default_wordlist}] (yes/no): "
        ).strip().lower()
        if use_default in ["yes", "y"]:
            if os.path.isfile(default_wordlist):
                print(f"[+] Using default wordlist: {default_wordlist}")
                return default_wordlist
            else:
                print(f"[!] Default wordlist not found at {default_wordlist}.")
        elif use_default in ["no", "n"]:
            custom_path = input("Enter the path to your custom wordlist: ").strip()
            if os.path.isfile(custom_path):
                print(f"[+] Using custom wordlist: {custom_path}")
                return custom_path
            else:
                print("[!] Wordlist file does not exist.")
        else:
            print("[!] Please answer 'yes' or 'no'.")
