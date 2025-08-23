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
    """Runs a system command and handles common errors."""
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
    """Checks the status of the systemd service."""
    print(f"Checking status of {SERVICE_NAME}...")
    run_system_command(["systemctl", "--user", "status", "--no-pager", SERVICE_NAME])

def service_start(args):
    """Starts the systemd service."""
    run_system_command(["systemctl", "--user", "start", SERVICE_NAME])
    print(f"{SERVICE_NAME} started.")

def service_stop(args):
    """Stops the systemd service."""
    run_system_command(["systemctl", "--user", "stop", SERVICE_NAME])
    print(f"{SERVICE_NAME} stopped.")

def service_restart(args):
    """Restarts the systemd service."""
    run_system_command(["systemctl", "--user", "restart", SERVICE_NAME])
    print(f"{SERVICE_NAME} restarted.")

def service_logs(args):
    """Follows the systemd service logs (journalctl)."""
    print(f"Showing systemd service logs for {SERVICE_NAME}... (Press Ctrl+C to exit)")
    try:
        subprocess.run(["journalctl", "--user", "-u", SERVICE_NAME, "-f", "-n", "50"])
    except KeyboardInterrupt:
        print("\nExiting log view.")

def app_logs(args):
    """Follows the application's persistent log file."""
    print(f"Showing application logs from: {LOG_FILE_PATH}")
    if not LOG_FILE_PATH.exists():
        print("Log file does not exist yet. It will be created when the service runs.")
        return
    
    print("Press Ctrl+C to exit.")
    try:
        # Use 'tail -f' to follow the log file in real-time
        subprocess.run(["tail", "-n", "100", "-f", str(LOG_FILE_PATH)])
    except KeyboardInterrupt:
        print("\nExiting log view.")

def check_gpu(args):
    """Checks if PyTorch can access a CUDA-enabled GPU."""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ GPU is available! Device: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ️ No GPU found. The service will run on the CPU.")
    except ImportError:
        print("❌ Error: PyTorch is not installed correctly.", file=sys.stderr)

def set_paths(args):
    """Sets configuration values in settings.ini."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    changes_made = False
    if args.input:
        abs_path = Path(args.input).expanduser().resolve()
        config["paths"]["input_dir"] = str(abs_path)
        print(f"Set input directory to: {abs_path}")
        changes_made = True
    # ... (rest of the set_paths function is the same)
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

    if changes_made:
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
        print("\n✅ Settings updated. Restart the service for changes to take effect:")
        print(f"   chromascale restart")
    else:
        print("No settings were changed. Use --input, --output, or --replace flags.")

def main():
    parser = argparse.ArgumentParser(description="ChromaScale CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Check the status of the watcher service.").set_defaults(func=service_status)
    subparsers.add_parser("start", help="Start the watcher service.").set_defaults(func=service_start)
    subparsers.add_parser("stop", help="Stop the watcher service.").set_defaults(func=service_stop)
    subparsers.add_parser("restart", help="Restart the watcher service.").set_defaults(func=service_restart)
    
    # RENAMED and NEW log commands
    subparsers.add_parser("service-logs", help="View the low-level systemd service logs.").set_defaults(func=service_logs)
    subparsers.add_parser("app-logs", help="View the high-level application job log file.").set_defaults(func=app_logs)

    subparsers.add_parser("check-gpu", help="Check for a CUDA-enabled GPU.").set_defaults(func=check_gpu)

    set_parser = subparsers.add_parser("set", help="Configure paths in settings.ini.")
    set_parser.add_argument("--input", type=str, help="Directory to watch for new images.")
    set_parser.add_argument("--output", type=str, help="Directory to save upscaled images.")
    set_parser.add_argument('--replace', dest='replace', action='store_true', help="Replace original files.")
    set_parser.add_argument('--no-replace', dest='replace', action='store_false', help="Save to output directory (default).")
    set_parser.set_defaults(replace=None, func=set_paths)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()