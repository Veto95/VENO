import random

def get_ascii_meme():
    memes = [
        r"""
     (\(\
    ( -.-)  *BEEP*
    o_(")(")  - Bunny deploying payload...
""",
        r"""
  ( ͡° ͜ʖ ͡°)つ──☆*:・ﾟ✧
  HACK THE PLANET, BABY
""",
        r"""
    ┌[ ⛧ ]─────────────
    │  SYSTEM BREACH
    └─> Root access granted
""",
        r"""
      .----.
     / .-"-.\
    | | '\ \ \
     \ \_\/ /_/
      '-._.-'
   INITIATING SCAN: STEALTH MODE
""",
        r"""
    ╔═╗┌─┐┬┌─┌─┐┌┬┐┬ ┬
    ╠═╝├┤ ├┴┐├┤  │ │ │
    ╩  └─┘┴ ┴└─┘ ┴ └─┘
    YOU'RE INSIDE. ACT NATURAL.
""",
        r"""
    (▀̿Ĺ̯▀̿ ̿)  
    WHO NEEDS PERMISSION?
    ACCESS GRANTED.
""",
        r"""
    █▄█ █▀█ ▄▀█ █▀▄ █ █▄░█ █▀▀
    █░█ █▀▄ █▀█ █▄▀ █ █░▀█ ██▄
    BUG HUNT ACTIVE
""",
        r"""
    ⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣷⣄
    ⠀⠀⢀⣴⣿⠿⠋⠁⠀⠀⠀⠈⠻⣿⣦
    ⠀⣾⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿
    ⢸⣿⡇⠀⠀⠀VENO DEPLOYED⠀⠀⢸⣿
    ⠘⣿⣧⣄⣀⣀⣀⣀⣀⣤⣴⣾⣿⠃
    ⠀⠉⠻⠿⣿⣿⣿⣿⣿⠿⠋
""",
        r"""
   ⠀⠀⠀⣀⣀⣀⣤⣤⣤⣤⣀⡀
   ⠀⣴⣿⠿⠿⠿⠿⢿⣿⣿⣿⣿⣦⡀
   ⣿⣿⡇⠀⠀⠀⠀⠀⠈⠙⣿⣿⣿⣿
   ⠉⠉⠀⠀⢀⣴⣿⣷⡄⠀⠀⠉⠉
   ↳ PAYLOAD READY. LET IT RIP.
""",
        r"""
   [0x01] NMAP LOADED
   [0x02] SQLMAP INIT
   [0x03] VENO ONLINE
   [OK] Let's break the internet.
""",
        r"""
    ☠ SYSTEM OVERRIDE ☠
    Root dance: (ง ͠° ͟ل͜ ͡°)ง
    BOOPING FIREWALLS SINCE 20XX
""",
        r"""
    ✧･ﾟ: *✧･ﾟ:* 　　 *:･ﾟ✧*:･ﾟ✧
     .----.     .--------.
    | == |     | VENO 🐍 |
    |----|     | ACTIVE  |
    '----'     '--------'
    ✧･ﾟ: *✧･ﾟ:* 　　 *:･ﾟ✧*:･ﾟ✧
""",
        r"""
  [🦠] RCE LAUNCHED
  [🔥] FIREWALL BYPASSED
  [💀] SYSADMIN SWEATING
""",
        r"""
   _______________________
  < VENO SAYS: STAY EVIL >
   -----------------------
          \   ^__^
           \  (oo)\_______
              (__)\       )\/\
                  ||----w |
                  ||     ||
""",
    ]
    return random.choice(memes)

def get_insult():
    lines = [
        "🐧 Linux is not a hobby. It's a personality.",
        "📡 If nmap was a religion, you'd be a high priest.",
        "🎯 Payload loaded. Target unaware. Hacker satisfied.",
        "👾 You don’t find bugs. They reveal themselves to you.",
        "🧠 grep, sed, awk — the holy trinity.",
        "📁 I came. I saw. I `ls -la`’d.",
        "🔥 Your exploit worked. The logs never knew.",
        "🐚 Real hackers don’t click — they curl.",
        "⚔️ WAFs fear what they can't parse.",
        "🛸 Hacked so clean, even the IDS said ‘respect’.",
        "🔍 You don’t brute force — you socially engineer the ports open.",
        "🧙‍♂️ Sudo gave you root. But Linux gave you purpose.",
        "☠️ `rm -rf /` is a love letter in hacker-speak.",
        "🌐 Every URL hides a secret. You’re the keymaster.",
        "🤫 Bash history never tells the full story.",
        "⚙️ If it runs `cron`, you already own it.",
        "📜 Logs are just confessionals for misconfigured servers.",
        "🐍 Python wasn’t made for hacking. You were.",
        "🔓 Uptime is just a countdown to your next shell.",
        "💻 They said it was patched. You said, 'Challenge accepted.'",
        "🕵️‍♂️ Dirbuster is just therapy with better wordlists.",
        "🚪 No vuln? No problem. You brute force the idea of access.",
        "💽 Hackers don’t die. They fork.",
        "💥 SIGKILL is how we say goodbye.",
        "🧨 One payload to rule them all. One misconfig to bind them.",
        "🔗 curl | bash. Because downloading responsibly is for civilians.",
        "🧃 Sipping coffee, piping stdout to glory.",
        "🧰 Tools don’t hack. Hackers bend tools to their will.",
        "🎮 Linux is the only game where root is the final boss.",
        "👣 `whoami` — identity crisis edition.",
        "🎙️ Logging out is for the weak. Real hackers `screen -d -r`.",
    ]
    return random.choice(lines)
