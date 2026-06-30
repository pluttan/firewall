#!/usr/bin/env python3
"""
vpnwall - Force applications to use VPN only.
If VPN is disconnected, blocked apps have no internet access.

Works by creating isolated users and using pf to filter traffic by user.
"""

import argparse
import json
import os
import subprocess
import sys
import pwd
import grp
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
PF_ANCHOR = "vpnwall"
PF_RULES_PATH = Path("/etc/pf.anchors/vpnwall")
VPNWALL_GROUP = "vpnwall"
USER_PREFIX = "_vpnwall_"
BASE_UID = 590  # Starting UID for vpnwall users


def load_config() -> dict:
    """Load configuration from JSON file."""
    if not CONFIG_PATH.exists():
        return {"vpn_interface": "utun+", "enabled": False, "apps": []}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save configuration to JSON file."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def user_exists(username: str) -> bool:
    """Check if a user exists."""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def group_exists(groupname: str) -> bool:
    """Check if a group exists."""
    try:
        grp.getgrnam(groupname)
        return True
    except KeyError:
        return False


def get_next_uid(config: dict) -> int:
    """Get next available UID for vpnwall users."""
    used_uids = [app.get("uid", 0) for app in config.get("apps", [])]
    uid = BASE_UID
    while uid in used_uids:
        uid += 1
    return uid


def sanitize_username(app_name: str) -> str:
    """Convert app name to valid username."""
    return USER_PREFIX + app_name.lower().replace(" ", "_").replace(".", "_")[:20]


def create_vpnwall_group() -> bool:
    """Create the vpnwall group if it doesn't exist."""
    if group_exists(VPNWALL_GROUP):
        return True
    
    try:
        # Find available GID
        gid = 590
        while True:
            try:
                grp.getgrgid(gid)
                gid += 1
            except KeyError:
                break
        
        run_cmd(["dscl", ".", "-create", f"/Groups/{VPNWALL_GROUP}"])
        run_cmd(["dscl", ".", "-create", f"/Groups/{VPNWALL_GROUP}", "PrimaryGroupID", str(gid)])
        run_cmd(["dscl", ".", "-create", f"/Groups/{VPNWALL_GROUP}", "RealName", "VPNWall Users"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to create group: {e}")
        return False


def create_user_for_app(app_name: str, uid: int) -> str | None:
    """Create a dedicated user for an application."""
    username = sanitize_username(app_name)
    
    if user_exists(username):
        return username
    
    try:
        # Create user
        run_cmd(["dscl", ".", "-create", f"/Users/{username}"])
        run_cmd(["dscl", ".", "-create", f"/Users/{username}", "UserShell", "/usr/bin/false"])
        run_cmd(["dscl", ".", "-create", f"/Users/{username}", "RealName", f"VPNWall: {app_name}"])
        run_cmd(["dscl", ".", "-create", f"/Users/{username}", "UniqueID", str(uid)])
        run_cmd(["dscl", ".", "-create", f"/Users/{username}", "PrimaryGroupID", "20"])  # staff group
        run_cmd(["dscl", ".", "-create", f"/Users/{username}", "NFSHomeDirectory", "/var/empty"])
        
        # Hide from login screen
        run_cmd(["dscl", ".", "-create", f"/Users/{username}", "IsHidden", "1"])
        
        return username
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to create user: {e}")
        return None


def delete_user(username: str) -> bool:
    """Delete a user."""
    if not user_exists(username):
        return True
    
    try:
        run_cmd(["dscl", ".", "-delete", f"/Users/{username}"])
        return True
    except subprocess.CalledProcessError:
        return False


def get_app_path(app_name: str) -> str | None:
    """Find application path."""
    paths = [
        f"/Applications/{app_name}.app",
        f"/Applications/{app_name}",
        os.path.expanduser(f"~/Applications/{app_name}.app"),
        f"/System/Applications/{app_name}.app",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def generate_pf_rules(config: dict) -> str:
    """Generate pf firewall rules based on config."""
    apps = config.get("apps", [])
    if not apps:
        return "# No apps configured\n"
    
    vpn_iface = config.get("vpn_interface", "utun+")
    
    rules = [
        "# vpnwall - VPN-only firewall rules",
        "# Auto-generated, do not edit manually",
        "",
    ]
    
    for app in apps:
        username = app.get("username")
        if not username:
            continue
        
        rules.append(f"# {app['name']} (user: {username})")
        # Block all traffic from this user
        rules.append(f"block out quick proto {{tcp, udp}} user {username}")
        # Allow traffic only through VPN interface
        rules.append(f"pass out quick on {vpn_iface} proto {{tcp, udp}} user {username}")
        rules.append("")
    
    return "\n".join(rules) + "\n"


def apply_pf_rules(config: dict) -> bool:
    """Apply pf rules."""
    rules = generate_pf_rules(config)
    
    try:
        # Write rules to anchor file
        PF_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PF_RULES_PATH, "w") as f:
            f.write(rules)
    except PermissionError:
        print("[!] Permission denied. Run with sudo.")
        return False
    
    # Check if anchor is in pf.conf
    pf_conf = Path("/etc/pf.conf")
    anchor_line = f'anchor "{PF_ANCHOR}"'
    load_anchor = f'load anchor "{PF_ANCHOR}" from "{PF_RULES_PATH}"'
    
    pf_content = pf_conf.read_text()
    if anchor_line not in pf_content:
        with open(pf_conf, "a") as f:
            f.write(f"\n{anchor_line}\n{load_anchor}\n")
    
    # Reload pf
    run_cmd(["pfctl", "-f", "/etc/pf.conf"], check=False)
    run_cmd(["pfctl", "-e"], check=False)
    
    return True


def cmd_add(args) -> int:
    """Add an application to the VPN-only list."""
    config = load_config()
    app_name = args.app
    
    # Check if already exists
    for app in config["apps"]:
        if app["name"].lower() == app_name.lower():
            print(f"[!] '{app_name}' already in the list")
            return 1
    
    # Check app exists
    app_path = get_app_path(app_name)
    if not app_path:
        print(f"[!] Application '{app_name}' not found")
        print("    Make sure the app exists in /Applications/")
        return 1
    
    # Create user for this app
    uid = get_next_uid(config)
    username = create_user_for_app(app_name, uid)
    
    if not username:
        print(f"[!] Failed to create user for '{app_name}'")
        return 1
    
    app_entry = {
        "name": app_name,
        "app_path": app_path,
        "username": username,
        "uid": uid,
    }
    
    config["apps"].append(app_entry)
    save_config(config)
    
    print(f"[+] Added '{app_name}'")
    print(f"    Path: {app_path}")
    print(f"    User: {username} (UID: {uid})")
    
    if config.get("enabled"):
        print("[*] Reloading firewall rules...")
        apply_pf_rules(config)
    
    print()
    print(f"[*] To run {app_name} through VPN only:")
    print(f"    sudo -u {username} open '{app_path}'")
    
    return 0


def cmd_remove(args) -> int:
    """Remove an application from the VPN-only list."""
    config = load_config()
    app_name = args.app
    
    for i, app in enumerate(config["apps"]):
        if app["name"].lower() == app_name.lower():
            username = app.get("username")
            if username:
                delete_user(username)
            
            config["apps"].pop(i)
            save_config(config)
            print(f"[-] Removed '{app_name}'")
            
            if config.get("enabled"):
                print("[*] Reloading firewall rules...")
                apply_pf_rules(config)
            return 0
    
    print(f"[!] '{app_name}' not found in the list")
    return 1


def cmd_list(args) -> int:
    """List all applications in the VPN-only list."""
    config = load_config()
    
    if not config.get("apps"):
        print("No applications configured.")
        print("Use 'sudo vpnwall add <AppName>' to add applications.")
        return 0
    
    print("Applications forced to use VPN only:")
    print("-" * 60)
    for app in config["apps"]:
        print(f"  {app['name']}")
        print(f"    Path: {app.get('app_path', 'N/A')}")
        print(f"    User: {app.get('username', 'N/A')}")
    print("-" * 60)
    print(f"VPN Interface: {config.get('vpn_interface', 'utun+')}")
    print(f"Firewall: {'ENABLED' if config.get('enabled') else 'DISABLED'}")
    
    return 0


def cmd_run(args) -> int:
    """Run an application through VPN only."""
    config = load_config()
    app_name = args.app
    
    # Find app in config
    app_entry = None
    for app in config["apps"]:
        if app["name"].lower() == app_name.lower():
            app_entry = app
            break
    
    if not app_entry:
        print(f"[!] '{app_name}' not in vpnwall list")
        print(f"    Add it first: sudo vpnwall add {app_name}")
        return 1
    
    if not config.get("enabled"):
        print("[!] Firewall is disabled. Enable it first: sudo vpnwall enable")
        return 1
    
    username = app_entry["username"]
    app_path = app_entry["app_path"]
    
    print(f"[*] Starting {app_name} as {username}...")
    
    # Run the app as the restricted user
    result = subprocess.run(
        ["sudo", "-u", username, "open", app_path],
        capture_output=False
    )
    
    return result.returncode


def cmd_enable(args) -> int:
    """Enable VPN-only firewall rules."""
    config = load_config()
    
    if not config.get("apps"):
        print("[!] No applications configured. Add apps first with 'sudo vpnwall add <AppName>'")
        return 1
    
    if apply_pf_rules(config):
        config["enabled"] = True
        save_config(config)
        print("[+] Firewall rules enabled")
        
        # Show VPN interface status
        result = run_cmd(["ifconfig"], check=False)
        vpn_iface = config.get("vpn_interface", "utun+").rstrip("+")
        vpn_active = vpn_iface in result.stdout
        
        if vpn_active:
            print(f"[*] VPN interface detected ({vpn_iface}*)")
        else:
            print(f"[!] Warning: No VPN interface detected. Apps will have no internet!")
        return 0
    return 1


def cmd_disable(args) -> int:
    """Disable VPN-only firewall rules."""
    config = load_config()
    
    # Clear anchor rules
    run_cmd(["pfctl", "-a", PF_ANCHOR, "-F", "all"], check=False)
    
    config["enabled"] = False
    save_config(config)
    print("[-] Firewall rules disabled")
    return 0


def cmd_status(args) -> int:
    """Show current status."""
    config = load_config()
    
    print("=== vpnwall status ===")
    print()
    
    # Firewall status
    enabled = config.get("enabled", False)
    print(f"Firewall: {'ENABLED' if enabled else 'DISABLED'}")
    print(f"VPN Interface: {config.get('vpn_interface', 'utun+')}")
    
    # Check VPN
    result = run_cmd(["ifconfig"], check=False)
    vpn_iface = config.get("vpn_interface", "utun+").rstrip("+")
    if vpn_iface in result.stdout:
        print(f"VPN Status: CONNECTED")
    else:
        print(f"VPN Status: DISCONNECTED")
    
    # Apps
    apps = config.get("apps", [])
    print()
    print(f"Configured apps: {len(apps)}")
    for app in apps:
        user_ok = user_exists(app.get("username", ""))
        status = "✓" if user_ok else "✗ user missing"
        print(f"  - {app['name']} ({app.get('username', 'N/A')}) {status}")
    
    # Show active pf rules
    if enabled:
        print()
        print("Active pf rules:")
        result = run_cmd(["pfctl", "-a", PF_ANCHOR, "-sr"], check=False)
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                print(f"  {line}")
        else:
            print("  (no rules loaded)")
    
    return 0


def cmd_set_interface(args) -> int:
    """Set VPN interface."""
    config = load_config()
    config["vpn_interface"] = args.interface
    save_config(config)
    print(f"[+] VPN interface set to: {args.interface}")
    
    if config.get("enabled"):
        print("[*] Reloading firewall rules...")
        apply_pf_rules(config)
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Force applications to use VPN only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo vpnwall add Arc          Add Arc to VPN-only list
  sudo vpnwall enable           Enable firewall rules  
  sudo vpnwall run Arc          Run Arc through VPN only
  sudo vpnwall status           Show current status
  sudo vpnwall disable          Disable firewall rules
  sudo vpnwall remove Arc       Remove Arc from list
  
  sudo vpnwall set-interface utun3   Set specific VPN interface
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # add
    add_parser = subparsers.add_parser("add", help="Add an application")
    add_parser.add_argument("app", help="Application name (e.g., Arc)")
    add_parser.set_defaults(func=cmd_add)
    
    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove an application")
    remove_parser.add_argument("app", help="Application name")
    remove_parser.set_defaults(func=cmd_remove)
    
    # list
    list_parser = subparsers.add_parser("list", help="List configured applications")
    list_parser.set_defaults(func=cmd_list)
    
    # run
    run_parser = subparsers.add_parser("run", help="Run an application through VPN only")
    run_parser.add_argument("app", help="Application name")
    run_parser.set_defaults(func=cmd_run)
    
    # enable
    enable_parser = subparsers.add_parser("enable", help="Enable firewall rules")
    enable_parser.set_defaults(func=cmd_enable)
    
    # disable
    disable_parser = subparsers.add_parser("disable", help="Disable firewall rules")
    disable_parser.set_defaults(func=cmd_disable)
    
    # status
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.set_defaults(func=cmd_status)
    
    # set-interface
    iface_parser = subparsers.add_parser("set-interface", help="Set VPN interface")
    iface_parser.add_argument("interface", help="Interface name (e.g., utun0 or utun+)")
    iface_parser.set_defaults(func=cmd_set_interface)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Check root for most commands
    if args.command not in ["list", "status"] and os.geteuid() != 0:
        print("[!] This command requires root. Run with sudo.")
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
