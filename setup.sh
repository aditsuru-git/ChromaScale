#!/usr/bin/env bash
set -euo pipefail

echo "=== ChromaScale Setup & Update Starting ==="

# --- Configuration ---
WORK_DIR="$HOME/.chromascale_home"
VENV_DIR="$WORK_DIR/.venv"
CLI_COMMAND_NAME="chromascale"
CLI_INSTALL_PATH="$HOME/.local/bin/$CLI_COMMAND_NAME"
SERVICE_NAME="chromascale"

# --- Pre-flight Checks ---

if ! command -v uv &> /dev/null; then
    echo "❌ ERROR: 'uv' is not installed or not in your PATH."
    echo "Please install it first. See: https://github.com/astral-sh/uv"
    exit 1
fi

if [[ ! ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo "⚠️ WARNING: '$HOME/.local/bin' is not in your PATH."
    echo "The '$CLI_COMMAND_NAME' command may not be available globally."
    echo "Please add it to your shell's configuration file (e.g., ~/.bashrc, ~/.zshrc):"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo ""
fi

# --- Installation & Update ---

echo "⚙️ Setting up working directory at '$WORK_DIR'..."
mkdir -p "$WORK_DIR"
mkdir -p "$(dirname "$CLI_INSTALL_PATH")"

echo "⚙️ Syncing application files to '$WORK_DIR'..."
rsync -a --delete --exclude='.git' --exclude='.venv' --exclude='__pycache__' "$(pwd)/" "$WORK_DIR/"

# Change to the working directory for all subsequent operations.
cd "$WORK_DIR"

# 1. Create the virtual environment
echo "⚙️ Creating/validating virtual environment with 'uv venv'..."
uv venv
echo "✅ Virtual environment is ready."

# 2. Activate the environment FOR THIS SCRIPT'S SESSION
echo "⚙️ Activating virtual environment for installation..."
source "$VENV_DIR/bin/activate"

# 3. Install dependencies from pyproject.toml
echo "⚙️ Installing dependencies using 'uv pip install'..."
uv pip install --requirements pyproject.toml
echo "✅ Dependencies are up to date."

# 4. Install the CLI command wrapper
echo "⚙️ Installing CLI command wrapper at '$CLI_INSTALL_PATH'..."
cat <<'EOF' > "$CLI_INSTALL_PATH"
#!/usr/bin/env bash
WORK_DIR="$HOME/.chromascale_home"
VENV_PYTHON="$WORK_DIR/.venv/bin/python"
CLI_SCRIPT="$WORK_DIR/src/cli.py"
"$VENV_PYTHON" "$CLI_SCRIPT" "$@"
EOF
chmod +x "$CLI_INSTALL_PATH"
echo "✅ CLI command '$CLI_COMMAND_NAME' is installed."

# 5. Create and enable systemd service
echo "⚙️ Setting up systemd user service '$SERVICE_NAME'..."
SERVICE_FILE="$HOME/.config/systemd/user/$SERVICE_NAME.service"
mkdir -p "$(dirname "$SERVICE_FILE")"

cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=ChromaScale Image Upscaling Watcher Service
After=network.target

[Service]
Type=simple
# CORRECTED: Use -m to run as a module, which fixes Python's import path.
ExecStart=$VENV_DIR/bin/python -m src.watcher
WorkingDirectory=$WORK_DIR
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOL

echo "⚙️ Reloading systemd daemon and restarting the service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"
systemctl --user restart "$SERVICE_NAME.service"

echo ""
echo "🎉 === ChromaScale Setup/Update Complete! ==="
echo "The service has been started/restarted to apply the latest changes."
echo "You can now manage the service using the global command:"
echo "  chromascale status"
echo "  chromascale logs"