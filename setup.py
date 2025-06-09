#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess

def is_global_command(cmd):
    return shutil.which(cmd) is not None

def launch_veno():
    try:
        subprocess.run(["veno"] + sys.argv[1:], check=False)
    except Exception as e:
        print(f"[!] Failed to launch veno: {e}")

def install_global_symlink():
    veno_path = os.path.abspath("veno.py")
    py_path = sys.executable
    bin_dir = "/usr/local/bin" if os.geteuid() == 0 else os.path.expanduser("~/.local/bin")
    target = os.path.join(bin_dir, "veno")

    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir, exist_ok=True)

    # Write a simple launcher shell script
    with open(target, "w") as f:
        f.write(f"#!/bin/sh\nexec {py_path} '{veno_path}' \"$@\"\n")
    os.chmod(target, 0o755)

    print(f"\n[✓] Symlink/launcher created: {target}")
    print("    You can now run VENO globally with: veno")
    if bin_dir not in os.environ.get("PATH", ""):
        print(f"    [!] Warning: {bin_dir} is not in your PATH. Add this to your shell profile.")

def main():
    if is_global_command("veno"):
        print("[✓] VENO is already globally available. Launching...")
        launch_veno()
        sys.exit(0)

    print("[-] VENO is not available globally. Setting up global launcher...")
    install_global_symlink()
    print("\n[✓] Done! Try running: veno")
    print("    (Restart your shell or source your profile if the command is not found)")

    # Optionally, launch veno now
    resp = input("Do you want to launch VENO now? [Y/n]: ").strip().lower()
    if resp in ("", "y", "yes"):
        launch_veno()

if __name__ == "__main__":
    main()
