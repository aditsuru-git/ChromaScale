#!/usr/bin/env python3
import sys
import subprocess
import configparser
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "settings.ini"

def status():
    subprocess.run(["systemctl", "status", "chromascale.service"])

def enable():
    subprocess.run(["systemctl", "enable", "--now", "chromascale.service"])

def disable():
    subprocess.run(["systemctl", "disable", "--now", "chromascale.service"])

def check_gpu():
    import torch
    device = "GPU" if torch.cuda.is_available() else "CPU"
    print(f"Using {device}")

def set_paths(input_dir=None, output_dir=None, replace_file=None):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    if input_dir:
        config["paths"]["input_dir"] = input_dir
    if output_dir:
        config["paths"]["output_dir"] = output_dir
    if replace_file is not None:
        config["paths"]["replace_file"] = str(replace_file)

    with open(CONFIG_PATH, "w") as f:
        config.write(f)
    print("Settings updated.")

def main():
    if len(sys.argv) < 2:
        print("Usage: image-upscaler <command> [args]")
        return

    cmd = sys.argv[1].lower()
    if cmd == "status":
        status()
    elif cmd == "enable":
        enable()
    elif cmd == "disable":
        disable()
    elif cmd == "check-gpu":
        check_gpu()
    elif cmd == "set":
        kwargs = {}
        for arg in sys.argv[2:]:
            if arg.startswith("input="):
                kwargs["input_dir"] = arg.split("=", 1)[1]
            elif arg.startswith("output="):
                kwargs["output_dir"] = arg.split("=", 1)[1]
            elif arg.startswith("replace="):
                kwargs["replace_file"] = arg.split("=", 1)[1].lower() == "true"
        set_paths(**kwargs)
    else:
        print("Unknown command.")

if __name__ == "__main__":
    main()
