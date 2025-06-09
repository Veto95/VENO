import random

def get_ascii_meme():
    memes = [
        r"""
     |\_/|                  
     | @ @   Woof!         
     |   <>              _ 
     |  _/\------____ ((| |))
     |               `--' |   
 ____|_       ___|   |___.' 
/_/_____/____/_______|
""",
        r"""
      ( ͡° ͜ʖ ͡°)つ──☆*:・ﾟ✧
      HACK THE PLANET
""",
        r"""
    ──────▄▄▄▄▄▄────────
    ──▄▄██████████▄▄────
    ▄████████████████▄──
    █████▀▀▀▀▀▀▀▀█████──
    ████▀░░░░░░░░▀████──
    ████▄░░░░░░░▄█████──
    ▀███████████████▀───
    ──▀███████████▀─────
    ──────▀▀▀▀▀─────────
      You got this!
""",
        r"""
     _____  _____  _____
    |  __ \|  __ \|  __ \
    | |__) | |__) | |__) |  OWNED
    |  ___/|  _  /|  ___/
    | |    | | \ \| |      
    |_|    |_|  \_\_|
""",
        r"""
    (╯°□°）╯︵ ┻━┻ 
    Flip a table, then flip some bugs!
""",
        r"""
       __      ___      _ 
      / /  ___| _ )_  _| |
     / /  (_-< _ \ || | |
    /_/  /__/___/\_,_|_|
    YOU ARE ROOT, DEAL WITH IT
""",
        r"""
    ┌( ಠ_ಠ)┘    ┌( ಠ_ಠ)┘    ┌( ಠ_ಠ)┘
      DANCE WHILE YOU SCAN!
""",
        r"""
           .--.
         .'_\/_'.
          '. /\ .'
            "||"
              ||
              ||
              XX
              XX
              XX
             XXXX
       ASCII CACTUS SAYS: HACK RESPONSIBLY
""",
        r"""
    (▀̿Ĺ̯▀̿ ̿)  SCAN COMPLETE. 
    YOU ARE THE DANGER.
""",
        r"""
    ──────────────▄██████████▄────────
    ────────▄███▓▓▓▓▓▓▓▓▓▓▓███▄──────
    ──────▄██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██─────
    ─────██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██─────
    ─────██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██─────
    ─────██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██─────
    ──────██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██──────
    ───────███▓▓▓▓▓▓▓▓▓▓▓▓███───────
    ─────────█████████████──────────
    HACKERMAN LEVEL: OVER 9000
""",
        r"""
    ⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣀⡀
    ⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣷⣄
    ⠀⠀⠀⣴⣿⣿⡿⠟⠛⠛⠻⠿⣿⣿⣿⣦
    ⠀⠀⣼⣿⡟⠁⠀⠀⠀⠀⠀⠀⠈⢻⣿⣿⣧
    ⠀⢸⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿
    ⠀⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿
    ⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
    ⠀⢿⣿⣦⣄⣀⣀⣀⣀⣤⣴⣾⣿⡿
    ⠀⠀⠙⠻⠿⣿⣿⣿⣿⡿⠿⠛⠁
    VENO SEES ALL. CODE HARDER.
""",
        r"""
   /\_/\  
  ( o.o ) 
   > ^ <    CAT SCANS YOUR BUGS
""",
        r"""
    _______________________
   /  SCANNING COMPLETE!  /
  /----------------------/
 /   (╯°□°）╯︵ ┻━┻     
/______________________/
""",
        r"""
    ＿人人人人人人人＿
    ＞　EXPLOIT TIME　＜
    ￣Y^Y^Y^Y^Y^Y^Y￣
""",
        r"""
   _____   _____ 
  / ____| |  __ \
 | |  __  | |__) |___   ___ 
 | | |_ | |  _  // _ \ / _ \
 | |__| | | | \ \ (_) |  __/
  \_____| |_|  \_\___/ \___|
   YOU CAN (AND WILL) HACK THIS
""",
        r"""
    (ノಠ益ಠ)ノ彡┻━┻
    TABLE FLIPPED. BUGS FEAR YOU.
""",
        r"""
    ┏(-_-)┛┗(-_-﻿ )┓┗(-_-)┛
    SCAN LIKE YOU MEAN IT!
""",
        r"""
    ¯\_(ツ)_/¯  NO VULNS? PATCH IT AGAIN
""",
        r"""
    (ง'̀-'́)ง    COME AT ME, CVEs!
""",
        r"""
    /////////////////
    //    HACK    //
    //   THE      //
    //  PLANET!   //
    /////////////////
""",
        r"""
    (☞ﾟヮﾟ)☞  YOU'RE A LEGEND
""",
        r"""
    ( •_•)>⌐■-■  (⌐■_■)
    SCANNING IN STYLE
""",
        r"""
    .----.
   /      \
  |        |
   \      /
    '----'
   THE BUG IS A LIE
""",
        r"""
    ░░░░░░░░░░░░░░░
    ░░░░▄░░░░▄░░░░░
    ░░░░░▀▄▀░░░░░░░
    ░░░░░░░░░░░░░░░
    LINUX PENGUIN BLESSING
""",
    ]
    return random.choice(memes)

def get_insult():
    insults = [
        "Scan complete. If you find bugs, buy yourself a cookie. If not, blame your wordlist.",
        "You just hacked the planet. Or at least you tried.",
        "Bugs found? Hell yeah! No bugs? Try harder.",
        "VENO finished. Go touch grass, nerd.",
        "Scan done! If there’s anything left, it’s probably a firewall. Or your fault.",
        "VENO: Making bug bounty hunters look good since right now.",
        "Another one bites the dust. Or maybe you just bit the dust. Check the report.",
        "You scan like a boss. Or at least like an intern with caffeine.",
        "VENO finished scanning. Your move, script kiddie.",
        "Report generated. Did you break the internet? If no, try again.",
        "If you didn't find anything, it's not VENO's fault. Blame the sysadmin.",
        "If you see this message, congrats! You're officially a professional button pusher.",
        "Another scan, another day closer to burnout.",
        "Scan finished. If you didn't break anything, you're not trying hard enough.",
        "You survived the scan. Now go outside and see the sun, you pale hacker.",
        "VENO says: 'Good job!' (But secretly, it did all the work.)"
    ]
    return random.choice(insults)
