#!/bin/bash

# -----------------------------
# ChromaScale Setup Script
# -----------------------------
APP_NAME="chromascale"
VENV_DIR="$HOME/.chromascale_venv"
SRC_DIR="$(pwd)/src"
MODEL_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
MODEL_PATH="$SRC_DIR/RealESRGAN_x4plus.pth"
CLI_LINK="$HOME/.local/bin/image-upscaler"

echo "=== ChromaScale Setup ==="

# -----------------------------
# 1. Create virtual environment
# -----------------------------
echo "Creating virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# -----------------------------
# 2. Install Python dependencies
# -----------------------------
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$SRC_DIR/requirements.txt"

# -----------------------------
# 3. Download RealESRGAN model
# -----------------------------
if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading RealESRGAN_x4plus.pth..."
    mkdir -p "$SRC_DIR"
    wget -O "$MODEL_PATH" "$MODEL_URL"
    echo "Model downloaded to $MODEL_PATH"
else
    echo "Model already exists at $MODEL_PATH"
fi

# -----------------------------
# 4. Make CLI globally executable
# -----------------------------
echo "Installing CLI command..."
chmod +x "$SRC_DIR/cli.py"
mkdir -p "$(dirname "$CLI_LINK")"
ln -sf "$SRC_DIR/cli.py" "$CLI_LINK"
echo "CLI installed as 'image-upscaler' (ensure $HOME/.local/bin is in PATH)"

# -----------------------------
# 5. Create systemd user service
# -----------------------------
SERVICE_FILE="$HOME/.config/systemd/user/$APP_NAME.service"
mkdir -p "$(dirname "$SERVICE_FILE")"

echo "Creating systemd service..."
cat > "$SERVICE_FILE" << EOL
[Unit]
Description=ChromaScale Image Upscaler
After=network.target

[Service]
Type=simple
ExecStart=$VENV_DIR/bin/python3 $SRC_DIR/watcher.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOL

# -----------------------------
# 6. Enable and start service
# -----------------------------
echo "Enabling and starting service..."
systemctl --user daemon-reload
systemctl --user enable --now "$APP_NAME.service"

echo "=== Setup Complete ==="
echo "Service is running. Use 'image-upscaler status' to check."
