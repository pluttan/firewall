![Header](header.png)

<div align="center">

# vpnwall

**macOS VPN kill-switch using per-app user isolation**

[![License](https://img.shields.io/badge/license-MIT-2C2C2C?style=for-the-badge&labelColor=1E1E1E)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-2C2C2C?style=for-the-badge&logo=python&labelColor=1E1E1E)]()
[![macOS](https://img.shields.io/badge/macos-10.15+-2C2C2C?style=for-the-badge&logo=apple&labelColor=1E1E1E)]()

</div>

Forces selected applications to route traffic exclusively through a VPN interface. When the VPN disconnects, blocked apps lose all internet access. Works by creating isolated macOS system users per app and using `pf` (packet filter) firewall rules to restrict their traffic to the VPN interface only.

## ■ Features

- ❖ **Per-app VPN enforcement** — each app runs under a dedicated system user
- ❖ **Kill-switch** — no VPN = no internet for configured apps
- ❖ **pf firewall rules** — blocks TCP/UDP by user, allows only via VPN interface
- ❖ **Flexible VPN interface** — supports specific utun or wildcard `utun+` matching
- ❖ **LaunchDaemon** — auto-enable on boot via included plist
- ❖ **JSON config** — persistent app registry in `config.json`
- ❖ **Hidden users** — system users with `_vpnwall_` prefix, hidden from login screen

## ■ Stack

| Component | Technology |
|-----------|------------|
| CLI | Python 3.10+ |
| Firewall | macOS pf (packet filter) |
| Config | JSON |
| Autostart | launchd (plist) |

## ■ Usage

```bash
# Add an app to VPN-only mode
sudo vpnwall add Arc

# Enable firewall rules
sudo vpnwall enable

# Run app through VPN
sudo vpnwall run Arc

# Check status
sudo vpnwall status

# Set VPN interface
sudo vpnwall set-interface utun3

# Disable / remove
sudo vpnwall disable
sudo vpnwall remove Arc
```

## ■ Screenshots

![Screenshot](screenshots/main.png)

## ■ License

MIT © [pluttan](https://github.com/pluttan)
