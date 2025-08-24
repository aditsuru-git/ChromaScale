#!/usr/bin/env python3
"""
ChromaScale CLI: A tool to manage and configure the ChromaScale service.
"""
import sys
import subprocess
import configparser
import argparse
from pathlib import Path

# --- Configuration ---
WORK_DIR = Path.home() / ".chromascale_home"
CONFIG_PATH = WORK_DIR / "src" / "settings.ini"
LOG_FILE_PATH = WORK_DIR / "chromascale.log"
SERVICE_NAME = "chromascale.service"

# --- Helper Functions ---
def run_system_command(command: list[str]):
    try:
        is_status_check = "status" in command
        subprocess.run(command, check=not is_status_check)
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}\n{e}", file=sys.stderr)
        sys.exit(1)

# --- CLI Command Functions ---
def service_status(args):
    print(f"Checking status of {SERVICE_NAME}...")
    run_system_command(["systemctl", "--user", "status", "--no-pager", SERVICE_NAME])

def service_start(args):
    run_system_command(["systemctl", "--user", "start", SERVICE_NAME])
    print(f"{SERVICE_NAME} started.")

def service_stop(args):
    run_system_command(["systemctl", "--user", "stop", SERVICE_NAME])
    print(f"{SERVICE_NAME} stopped.")

def service_restart(args):
    run_system_command(["systemctl", "--user", "restart", SERVICE_NAME])
    print(f"{SERVICE_NAME} restarted.")

def service_logs(args):
    print(f"Showing systemd service logs for {SERVICE_NAME}... (Press Ctrl+C to exit)")
    try:
        subprocess.run(["journalctl", "--user", "-u", SERVICE_NAME, "-f", "-n", "50"])
    except KeyboardInterrupt:
        print("\nExiting log view.")

def app_logs(args):
    print(f"Showing application logs from: {LOG_FILE_PATH}")
    if not LOG_FILE_PATH.exists():
        print("Log file does not exist yet. It will be created when the service runs.")
        return
    print("Press Ctrl+C to exit.")
    try:
        subprocess.run(["tail", "-n", "100", "-f", str(LOG_FILE_PATH)])
    except KeyboardInterrupt:
        print("\nExiting log view.")

def check_gpu(args):
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ GPU is available! Device: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ️ No GPU found. The service will run on the CPU.")
    except ImportError:
        print("❌ Error: PyTorch is not installed correctly.", file=sys.stderr)

# --- UPDATED set_paths function ---
def set_paths(args):
    """Sets configuration values in settings.ini."""
    # Ensure config section exists
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        config = configparser.ConfigParser()
        config["paths"] = {}
    else:
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        if "paths" not in config:
            config["paths"] = {}

    changes_made = False
    if args.input:
        abs_path = Path(args.input).expanduser().resolve()
        config["paths"]["input_dir"] = str(abs_path)
        print(f"Set input directory to: {abs_path}")
        changes_made = True
    if args.output:
        abs_path = Path(args.output).expanduser().resolve()
        config["paths"]["output_dir"] = str(abs_path)
        print(f"Set output directory to: {abs_path}")
        changes_made = True
    if args.replace is not None:
        replace_str = "true" if args.replace else "false"
        config["paths"]["replace_file"] = replace_str
        print(f"Set replace file to: {replace_str}")
        changes_made = True
    
    # NEW: Handle device mode setting
    if args.device:
        config["paths"]["device_mode"] = args.device
        print(f"Set processing device to: {args.device}")
        changes_made = True
    
    # NEW: Handle skip threshold setting
    if args.threshold is not None:
        config["paths"]["skip_resolution_threshold"] = str(args.threshold)
        print(f"Set skip threshold to: {args.threshold}px")
        changes_made = True

    if changes_made:
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
        print("\n✅ Settings updated. Restart the service for changes to take effect:")
        print(f"   chromascale restart")
    else:
        print("No settings were changed. Use flags like --input, --device, etc.")

def main():
    parser = argparse.ArgumentParser(description="ChromaScale CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Check the status of the watcher service.").set_defaults(func=service_status)
    subparsers.add_parser("start", help="Start the watcher service.").set_defaults(func=service_start)
    subparsers.add_parser("stop", help="Stop the watcher service.").set_defaults(func=service_stop)
    subparsers.add_parser("restart", help="Restart the watcher service.").set_defaults(func=service_restart)
    subparsers.add_parser("service-logs", help="View the low-level systemd service logs.").set_defaults(func=service_logs)
    subparsers.add_parser("app-logs", help="View the high-level application job log file.").set_defaults(func=app_logs)
    subparsers.add_parser("check-gpu", help="Check for a CUDA-enabled GPU.").set_defaults(func=check_gpu)

    # --- UPDATED set_parser ---
    set_parser = subparsers.add_parser("set", help="Configure paths, device, and other settings in settings.ini.")
    set_parser.add_argument("--input", type=str, help="Directory to watch for new images.")
    set_parser.add_argument("--output", type=str, help="Directory to save upscaled images.")
    set_parser.add_argument('--replace', dest='replace', action='store_true', help="Replace original files.")
    set_parser.add_argument('--no-replace', dest='replace', action='store_false', help="Save to output directory (default).")
    # NEW arguments
    set_parser.add_argument('--device', type=str, choices=['auto', 'cpu', 'cuda'], help="Set processing device. 'auto' uses GPU if available.")
    set_parser.add_argument('--threshold', type=int, help="Skip upscaling images where width or height is above this pixel value.")
    
    set_parser.set_defaults(replace=None, func=set_paths)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()