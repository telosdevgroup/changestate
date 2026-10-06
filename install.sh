#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/changestate"
BIN_TARGET="/usr/local/bin/changestate"
AUTO_BIN_TARGET="/usr/local/bin/changestate-auto"
SERVICE_TARGET="/etc/systemd/system/changestate-auto.service"

echo "============================================================"
echo "          ChangeState & changestate-auto Installer          "
echo "============================================================"

# Check system dependencies
command -v python3 >/dev/null 2>&1 || { echo >&2 "[ERROR] python3 is required. Aborting."; exit 1; }

# Determine if running from a local git clone or remote curl
SCRIPT_DIR=""
if [ -f "./changestate" ] && [ -d "./changestate_core" ]; then
    SCRIPT_DIR="$(pwd)"
elif [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
    if [ -f "$DIR/changestate" ] && [ -d "$DIR/changestate_core" ]; then
        SCRIPT_DIR="$DIR"
    fi
fi

if [ -n "$SCRIPT_DIR" ]; then
    echo "• Installing from local repository directory: $SCRIPT_DIR"
    sudo mkdir -p /usr/local/bin
    sudo ln -sf "$SCRIPT_DIR/changestate" "$BIN_TARGET"
    sudo chmod +x "$BIN_TARGET"
    echo "✓ ChangeState CLI linked to $BIN_TARGET"

    if [ -f "$SCRIPT_DIR/changestate-auto" ]; then
        sudo ln -sf "$SCRIPT_DIR/changestate-auto" "$AUTO_BIN_TARGET"
        sudo chmod +x "$AUTO_BIN_TARGET"
        echo "✓ ChangeState Auto daemon linked to $AUTO_BIN_TARGET"
    fi

    if [ -f "$SCRIPT_DIR/changestate-auto.service" ]; then
        sudo cp "$SCRIPT_DIR/changestate-auto.service" "$SERVICE_TARGET"
        sudo systemctl daemon-reload
        echo "✓ ChangeState Auto service installed to $SERVICE_TARGET"
    fi

    if [ -f "$SCRIPT_DIR/extras/battery-guard" ]; then
        sudo ln -sf "$SCRIPT_DIR/extras/battery-guard" /usr/local/bin/battery-guard
        sudo chmod +x /usr/local/bin/battery-guard
        echo "✓ BatteryGuard utility linked to /usr/local/bin/battery-guard"
    fi
else
    echo "• Fetching latest ChangeState from GitHub..."
    TMP_DIR=$(mktemp -d /tmp/changestate-install.XXXXXX)
    trap 'rm -rf "$TMP_DIR"' EXIT

    git clone --depth 1 https://github.com/telosdevgroup/changestate.git "$TMP_DIR/changestate"

    echo "• Installing ChangeState engine to $INSTALL_DIR..."
    sudo rm -rf "$INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
    sudo cp -r "$TMP_DIR/changestate/changestate" "$TMP_DIR/changestate/changestate_core" "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/changestate"
    sudo ln -sf "$INSTALL_DIR/changestate" "$BIN_TARGET"
    echo "✓ ChangeState CLI installed to $BIN_TARGET"

    if [ -f "$TMP_DIR/changestate/changestate-auto" ]; then
        sudo cp "$TMP_DIR/changestate/changestate-auto" "$INSTALL_DIR/"
        sudo chmod +x "$INSTALL_DIR/changestate-auto"
        sudo ln -sf "$INSTALL_DIR/changestate-auto" "$AUTO_BIN_TARGET"
        echo "✓ ChangeState Auto daemon installed to $AUTO_BIN_TARGET"
    fi

    if [ -f "$TMP_DIR/changestate/changestate-auto.service" ]; then
        sudo cp "$TMP_DIR/changestate/changestate-auto.service" "$SERVICE_TARGET"
        sudo systemctl daemon-reload
        echo "✓ ChangeState Auto service installed to $SERVICE_TARGET"
    fi

    if [ -f "$TMP_DIR/changestate/extras/battery-guard" ]; then
        sudo mkdir -p "$INSTALL_DIR/extras"
        sudo cp "$TMP_DIR/changestate/extras/battery-guard" "$INSTALL_DIR/extras/"
        sudo chmod +x "$INSTALL_DIR/extras/battery-guard"
        sudo ln -sf "$INSTALL_DIR/extras/battery-guard" /usr/local/bin/battery-guard
        echo "✓ BatteryGuard utility installed to /usr/local/bin/battery-guard"
    fi
fi

echo ""
echo "============================================================"
echo "Installation complete!"
echo "• Test CLI with: changestate status"
echo "• Enable Auto Daemon: sudo systemctl enable --now changestate-auto"
echo "• Check Auto Status: systemctl status changestate-auto"
echo "============================================================"
