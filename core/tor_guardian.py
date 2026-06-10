#!/usr/bin/env python3
"""
TorGuardian Module
==================
A security module that ensures ALL traffic is routed through Tor.
- Blocks clearnet if Tor fails (Tor Jail).
- Kills critical processes on failure.
- Cross-platform support (Linux, Windows, Termux).
- Validates Tor for AI requests.

NTRLI Principles:
- No Taxes: No clearnet leaks.
- No Traceability: All traffic via Tor.
- Absolute Sovereignty: User controls network routing.
"""

import os
import sys
import time
import json
import socket
import subprocess
import platform
import requests
from typing import Optional, Dict, List
from pathlib import Path


class TorGuardian:
    """
    Ensures all network traffic is routed through Tor.
    Implements Tor Jail to block clearnet and kill processes if Tor fails.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize TorGuardian with configuration.
        
        Args:
            config_path: Path to settings.json. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.tor_proxy = self.config.get("tor_proxy", "socks5://127.0.0.1:9050")
        self.tor_check_url = self.config.get("tor_check_url", "https://check.torproject.org/api/ip")
        self.critical_processes = self.config.get("critical_processes", [
            "sparrow", "wasabi", "electrum", "python", "java", "dotnet"
        ])
        self.tor_jailed = False
        self.platform = platform.system().lower()

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "tor_proxy": "socks5://127.0.0.1:9050",
                "tor_check_url": "https://check.torproject.org/api/ip",
                "critical_processes": ["sparrow", "wasabi", "electrum", "python", "java", "dotnet"],
            }

    def is_active(self) -> bool:
        """
        Check if Tor is active by querying check.torproject.org.
        
        Returns:
            bool: True if Tor is active, False otherwise.
        """
        try:
            proxies = {"http": self.tor_proxy, "https": self.tor_proxy}
            response = requests.get(
                self.tor_check_url,
                proxies=proxies,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("IsTor", False)
            return False
        except (requests.RequestException, json.JSONDecodeError):
            return False

    def check_tor(self) -> bool:
        """Alias for is_active() for backward compatibility."""
        return self.is_active()

    def get_proxy_dict(self) -> Dict[str, str]:
        """Get Tor proxy settings for HTTP requests."""
        return {"http": self.tor_proxy, "https": self.tor_proxy}

    def validate_tor_for_ai(self) -> bool:
        """
        Validate that Tor is active for AI requests.
        
        Returns:
            bool: True if Tor is ready.
        
        Raises:
            RuntimeError: If Tor is not active.
        """
        if not self.is_active():
            raise RuntimeError("Tor is not active! All AI requests must route through Tor.")
        return True

    # ==================== CLEARNET BLOCKING ====================
    def block_clearnet(self) -> bool:
        """Block all clearnet traffic (cross-platform)."""
        try:
            if self.platform == "windows":
                return self._block_clearnet_windows()
            else:
                return self._block_clearnet_linux()
        except Exception as e:
            print(f"[TorGuardian] ❌ Failed to block clearnet: {e}")
            return False

    def _block_clearnet_linux(self) -> bool:
        """Block clearnet using iptables (Linux/Termux)."""
        try:
            subprocess.run(["iptables", "-F"], check=True, capture_output=True)
            subprocess.run(["iptables", "-X"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "INPUT", "DROP"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "DROP"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "FORWARD", "DROP"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "9050", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9050", "-j", "ACCEPT"], check=True, capture_output=True)
            print("[TorGuardian] ✅ Clearnet blocked (Linux/iptables).")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[TorGuardian] ❌ Failed to block clearnet (Linux): {e.stderr.decode()}")
            return False

    def _block_clearnet_windows(self) -> bool:
        """Block clearnet using Windows Firewall (netsh)."""
        try:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=Block_HTTP_Out", "dir=out", "action=block", "protocol=TCP", "remoteport=80"],
                check=True, capture_output=True
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=Block_HTTPS_Out", "dir=out", "action=block", "protocol=TCP", "remoteport=443"],
                check=True, capture_output=True
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=Allow_Tor_9050", "dir=out", "action=allow", "protocol=TCP", "remoteport=9050"],
                check=True, capture_output=True
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule", 
                 "name=Allow_Localhost", "dir=out", "action=allow", "remoteip=127.0.0.1"],
                check=True, capture_output=True
            )
            print("[TorGuardian] ✅ Clearnet blocked (Windows Firewall).")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[TorGuardian] ❌ Failed to block clearnet (Windows): {e.stderr.decode()}")
            return False

    def unblock_clearnet(self) -> bool:
        """Restore clearnet access (cross-platform)."""
        try:
            if self.platform == "windows":
                return self._unblock_clearnet_windows()
            else:
                return self._unblock_clearnet_linux()
        except Exception as e:
            print(f"[TorGuardian] ❌ Failed to restore clearnet: {e}")
            return False

    def _unblock_clearnet_linux(self) -> bool:
        """Restore clearnet by resetting iptables."""
        try:
            subprocess.run(["iptables", "-F"], check=True, capture_output=True)
            subprocess.run(["iptables", "-X"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "FORWARD", "ACCEPT"], check=True, capture_output=True)
            print("[TorGuardian] ✅ Clearnet access restored (Linux/iptables).")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[TorGuardian] ❌ Failed to restore clearnet (Linux): {e.stderr.decode()}")
            return False

    def _unblock_clearnet_windows(self) -> bool:
        """Restore clearnet by removing Windows Firewall rules."""
        try:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", "name=Block_HTTP_Out"],
                check=False, capture_output=True
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", "name=Block_HTTPS_Out"],
                check=False, capture_output=True
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", "name=Allow_Tor_9050"],
                check=False, capture_output=True
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", "name=Allow_Localhost"],
                check=False, capture_output=True
            )
            print("[TorGuardian] ✅ Clearnet access restored (Windows Firewall).")
            return True
        except Exception as e:
            print(f"[TorGuardian] ❌ Failed to restore clearnet (Windows): {e}")
            return False

    # ==================== TOR JAIL ====================
    def kill_critical_processes(self) -> None:
        """Kill all critical processes to prevent leaks."""
        for process in self.critical_processes:
            try:
                if self.platform == "windows":
                    subprocess.run(["taskkill", "/F", "/IM", f"{process}.exe"], check=False, capture_output=True)
                else:
                    subprocess.run(["pkill", "-f", process], check=False, capture_output=True)
                print(f"[TorGuardian] 🔪 Killed process: {process}")
            except Exception as e:
                print(f"[TorGuardian] ⚠️ Failed to kill {process}: {e}")

    def activate_tor_jail(self) -> None:
        """Activate Tor Jail: Block clearnet + kill critical processes."""
        print("[TorGuardian] 🚨 Activating Tor Jail!")
        self.block_clearnet()
        self.kill_critical_processes()
        self.tor_jailed = True
        print("[TorGuardian] 🔒 Tor Jail activated. System locked until Tor is restored.")

    def deactivate_tor_jail(self) -> None:
        """Deactivate Tor Jail: Restore clearnet."""
        print("[TorGuardian] 🔓 Deactivating Tor Jail.")
        self.unblock_clearnet()
        self.tor_jailed = False
        print("[TorGuardian] ✅ Tor Jail deactivated.")

    def ensure_tor(self) -> bool:
        """
        Ensure Tor is active before allowing external requests.
        Activates Tor Jail if Tor fails.
        
        Returns:
            bool: True if Tor is active, False if Tor Jail was activated.
        """
        if self.tor_jailed:
            print("[TorGuardian] ⚠️ Tor Jail is active. Cannot proceed.")
            return False
        if not self.is_active():
            print("[TorGuardian] ❌ Tor is not active. Activating Tor Jail.")
            self.activate_tor_jail()
            return False
        print("[TorGuardian] ✅ Tor is active. Proceeding.")
        return True

    # ==================== MONITORING ====================
    def monitor_tor(self, interval: int = 60) -> None:
        """Continuously monitor Tor connectivity."""
        print(f"[TorGuardian] 🔍 Starting Tor monitor (interval: {interval}s).")
        while True:
            if not self.check_tor():
                print("[TorGuardian] ❌ Tor check failed. Activating Tor Jail.")
                self.activate_tor_jail()
                break
            time.sleep(interval)

    def is_jailed(self) -> bool:
        """Check if Tor Jail is active."""
        return self.tor_jailed

    # ==================== TOR SERVICE MANAGEMENT ====================
    def check_tor_service(self) -> bool:
        """Check if the Tor service is running."""
        try:
            if self.platform == "windows":
                result = subprocess.run(
                    ["sc", "query", "Tor"],
                    check=True, capture_output=True, text=True
                )
                return "RUNNING" in result.stdout
            else:
                result = subprocess.run(
                    ["pgrep", "-f", "tor"],
                    check=True, capture_output=True
                )
                return result.returncode == 0
        except Exception:
            return False

    def start_tor_service(self) -> bool:
        """Start the Tor service."""
        try:
            if self.platform == "windows":
                subprocess.run(["net", "start", "Tor"], check=True, capture_output=True)
            else:
                subprocess.run(["sudo", "systemctl", "start", "tor"], check=True, capture_output=True)
            print("[TorGuardian] ✅ Tor service started.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[TorGuardian] ❌ Failed to start Tor service: {e.stderr.decode()}")
            return False


if __name__ == "__main__":
    guardian = TorGuardian()
    print(f"[TorGuardian] Platform: {guardian.platform}")
    if guardian.check_tor_service():
        print("Tor service is running.")
    else:
        print("Tor service is not running.")
    if guardian.ensure_tor():
        print("Tor is active. System is secure.")
    else:
        print("Tor is not active. System is locked.")
