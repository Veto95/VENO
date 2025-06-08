import os

def get_wordlist(outdir):
    while True:
        wordlist = input("Enter path to wordlist: ").strip()
        if os.path.isfile(wordlist):
            return wordlist
        print("[!] Wordlist file does not exist.")
