<div align="center">

# vpnwall

**macOS VPN kill-switch using per-app user isolation**


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

<div align="center">

| Component | Technology |
|-----------|------------|
| CLI | Python 3.10+ |
| Firewall | macOS pf (packet filter) |
| Config | JSON |
| Autostart | launchd (plist) |

</div>

## ■ How It Works

```
1. Add an app — creates a dedicated `_vpnwall_` system user and registers it in config.json.
2. Enable firewall — loads pf rules that restrict each app user's TCP/UDP traffic to the VPN interface only.
3. Run the app — launches it under its dedicated isolated system user.
4. Kill-switch — if the VPN disconnects, pf blocks all outbound traffic for configured app users.
5. Boot persistence — LaunchDaemon auto-enables the firewall rules on every system start.
```

## ■ Screenshots

<div align="center">

![Screenshot](screenshots/main.png)

*Main interface showing VPN kill-switch status and configured apps*

</div>

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

## ■ License

MIT © [pluttan](https://github.com/pluttan)
