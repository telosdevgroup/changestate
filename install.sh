#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_URL="https://raw.githubusercontent.com/telosdevgroup/changestate/main"
INSTALL_DIR="/opt/changestate"
BIN_TARGET="/usr/local/bin/changestate"
APPLET_UUID="changestate@avathings.com"
APPLET_TARGET_DIR="$HOME/.local/share/cinnamon/applets/$APPLET_UUID"

echo "============================================================"
echo "          ChangeState Installer & Applet Setup             "
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

    mkdir -p "$(dirname "$APPLET_TARGET_DIR")"
    ln -sfn "$SCRIPT_DIR/cinnamon-applet/$APPLET_UUID" "$APPLET_TARGET_DIR"
    echo "✓ Cinnamon applet linked to $APPLET_TARGET_DIR"
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

    mkdir -p "$(dirname "$APPLET_TARGET_DIR")"
    rm -rf "$APPLET_TARGET_DIR"
    cp -r "$TMP_DIR/changestate/cinnamon-applet/$APPLET_UUID" "$APPLET_TARGET_DIR"
    echo "✓ Cinnamon applet installed to $APPLET_TARGET_DIR"
fi

echo ""
echo "============================================================"
echo "Installation complete!"
echo "• Test CLI with: changestate status"
echo "• Add Applet: Right-click Cinnamon Panel -> Applets -> ChangeState"
echo "  (or restart Cinnamon panel with Alt+F2 -> r -> Enter)"
echo "============================================================"
