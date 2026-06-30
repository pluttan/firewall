#!/bin/bash
# vpnwall installer

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/local/bin"
PLIST_DIR="/Library/LaunchDaemons"

echo "=== vpnwall Installer ==="
echo

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy main script
cp "$SCRIPT_DIR/vpnwall.py" "$INSTALL_DIR/vpnwall"
chmod +x "$INSTALL_DIR/vpnwall"
echo "[+] Installed vpnwall to $INSTALL_DIR/vpnwall"

# Copy config (preserve existing if present)
if [[ ! -f "$INSTALL_DIR/config.json" ]]; then
    cp "$SCRIPT_DIR/config.json" "$INSTALL_DIR/config.json"
    echo "[+] Created config at $INSTALL_DIR/config.json"
else
    echo "[*] Config already exists, keeping existing"
fi

# Install LaunchDaemon
cp "$SCRIPT_DIR/com.vpnwall.plist" "$PLIST_DIR/"
chown root:wheel "$PLIST_DIR/com.vpnwall.plist"
chmod 644 "$PLIST_DIR/com.vpnwall.plist"
echo "[+] Installed LaunchDaemon"

# Load LaunchDaemon
launchctl load "$PLIST_DIR/com.vpnwall.plist" 2>/dev/null || true
echo "[+] LaunchDaemon loaded"

echo
echo "=== Installation complete ==="
echo
echo "Usage:"
echo "  sudo vpnwall add Telegram    # Add app to VPN-only list"
echo "  sudo vpnwall list            # Show configured apps"
echo "  sudo vpnwall enable          # Enable firewall rules"
echo "  sudo vpnwall status          # Show status"
echo
