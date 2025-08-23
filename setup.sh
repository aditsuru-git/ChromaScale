#!/usr/bin/env bash
set -euo pipefail

echo "=== ChromaScale Setup & Update Starting ==="

# --- Configuration ---
WORK_DIR="$HOME/.chromascale_home"
VENV_DIR="$WORK_DIR/.venv"
CLI_COMMAND_NAME="chromascale"
CLI_INSTALL_PATH="$HOME/.local/bin/$CLI_COMMAND_NAME"
SERVICE_NAME="chromascale"
MODEL_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
MODEL_FILENAME="RealESRGAN_x4plus.pth"

# --- Pre-flight Checks ---

if ! command -v uv &> /dev/null; then
    echo "❌ ERROR: 'uv' is not installed or not in your PATH."
    exit 1
fi
if ! command -v curl &> /dev/null; then
    echo "❌ ERROR: 'curl' is not installed. Please install it (e.g., 'sudo apt install curl')."
    exit 1
fi

if [[ ! ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo "⚠️ WARNING: '$HOME/.local/bin' is not in your PATH."
fi

# --- Installation & Update ---

echo "⚙️ Setting up working directory at '$WORK_DIR'..."
mkdir -p "$WORK_DIR"
mkdir -p "$(dirname "$CLI_INSTALL_PATH")"

echo "⚙️ Syncing application files to '$WORK_DIR'..."
rsync -a --delete --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude="$MODEL_FILENAME" "$(pwd)/" "$WORK_DIR/"

cd "$WORK_DIR"

# --- Robust Model Download Step ---
if [ ! -f "$MODEL_FILENAME" ]; then
    echo "⚙️ Model weights not found. Downloading '$MODEL_FILENAME'..."
    # Download to a temporary file first to ensure atomicity.
    # --fail makes curl exit with an error if the download fails (e.g., 404).
    # The `&&` ensures the `mv` only happens if curl succeeds.
    curl -L --fail -o "$MODEL_FILENAME.tmp" "$MODEL_URL" && \
    mv "$MODEL_FILENAME.tmp" "$MODEL_FILENAME"
    echo "✅ Model downloaded successfully."
else
    echo "✅ Model weights already exist. Skipping download."
fi

# --- Python Environment Setup ---
echo "⚙️ Creating/validating virtual environment with 'uv venv'..."
uv venv
echo "✅ Virtual environment is ready."

echo "⚙️ Activating virtual environment for installation..."
source "$VENV_DIR/bin/activate"

echo "⚙️ Installing dependencies using 'uv pip install'..."
uv pip install --requirements pyproject.toml
echo "✅ Dependencies are up to date."

# --- CLI & Service Setup ---
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

echo "⚙️ Setting up systemd user service '$SERVICE_NAME'..."
SERVICE_FILE="$HOME/.config/systemd/user/$SERVICE_NAME.service"
mkdir -p "$(dirname "$SERVICE_FILE")"

cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=ChromaScale Image Upscaling Watcher Service
After=network.target

[Service]
Type=simple
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