#!/usr/bin/env python3
"""
TorGuardian Module
==================
A security module that ensures ALL traffic is routed through Tor.
- Blocks clearnet if Tor fails.
- Activates Tor Jail (kills critical processes, blocks traffic) on failure.
- Monitors Tor connectivity continuously.
"""

import os
import sys
import time
import json
import socket
import subprocess
import requests
from typing import Optional, Dict, List
from pathlib import Path


class TorGuardian:
    """
    Ensures all network traffic is routed through Tor.
    Implements Tor Jail to block clearnet and kill critical processes if Tor fails.
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
        self.critical_processes = self.config.get("critical_processes", [])
        self.tor_jailed = False

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

    def check_tor(self) -> bool:
        """
        Check if Tor is active by querying check.torproject.org.
        
        Returns:
            bool: True if Tor is active, False otherwise.
        """
        try:
            # Configure requests to use Tor proxy
            proxies = {
                "http": self.tor_proxy,
                "https": self.tor_proxy,
            }
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

    def block_clearnet(self) -> bool:
        """
        Block all clearnet traffic using iptables.
        Allows only localhost (127.0.0.1) traffic.
        
        Returns:
            bool: True if blocking was successful, False otherwise.
        """
        try:
            # Flush existing rules
            subprocess.run(["iptables", "-F"], check=True, capture_output=True)
            subprocess.run(["iptables", "-X"], check=True, capture_output=True)
            
            # Set default policies to DROP
            subprocess.run(["iptables", "-P", "INPUT", "DROP"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "DROP"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "FORWARD", "DROP"], check=True, capture_output=True)
            
            # Allow localhost traffic
            subprocess.run(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=True, capture_output=True)
            
            # Allow established connections
            subprocess.run(["iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True, capture_output=True)
            
            # Allow Tor traffic (SOCKS5 port 9050)
            subprocess.run(["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "9050", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9050", "-j", "ACCEPT"], check=True, capture_output=True)
            
            print("[TorGuardian] ✅ Clearnet blocked. Only Tor traffic allowed.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[TorGuardian] ❌ Failed to block clearnet: {e.stderr.decode()}")
            return False

    def unblock_clearnet(self) -> bool:
        """
        Restore clearnet access by resetting iptables.
        
        Returns:
            bool: True if unblocking was successful, False otherwise.
        """
        try:
            subprocess.run(["iptables", "-F"], check=True, capture_output=True)
            subprocess.run(["iptables", "-X"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["iptables", "-P", "FORWARD", "ACCEPT"], check=True, capture_output=True)
            print("[TorGuardian] ✅ Clearnet access restored.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[TorGuardian] ❌ Failed to restore clearnet: {e.stderr.decode()}")
            return False

    def kill_critical_processes(self) -> None:
        """
        Kill all critical processes to prevent leaks.
        """
        for process in self.critical_processes:
            try:
                subprocess.run(["pkill", "-f", process], check=False, capture_output=True)
                print(f"[TorGuardian] 🔪 Killed process: {process}")
            except Exception as e:
                print(f"[TorGuardian] ⚠️ Failed to kill {process}: {e}")

    def activate_tor_jail(self) -> None:
        """
        Activate Tor Jail:
        - Block clearnet.
        - Kill critical processes.
        - Set tor_jailed flag.
        """
        print("[TorGuardian] 🚨 Activating Tor Jail!")
        self.block_clearnet()
        self.kill_critical_processes()
        self.tor_jailed = True
        print("[TorGuardian] 🔒 Tor Jail activated. System locked until Tor is restored.")

    def deactivate_tor_jail(self) -> None:
        """
        Deactivate Tor Jail:
        - Restore clearnet.
        - Reset tor_jailed flag.
        """
        print("[TorGuardian] 🔓 Deactivating Tor Jail.")
        self.unblock_clearnet()
        self.tor_jailed = False
        print("[TorGuardian] ✅ Tor Jail deactivated.")

    def ensure_tor(self) -> bool:
        """
        Ensure Tor is active before allowing external requests.
        If Tor fails, activate Tor Jail.
        
        Returns:
            bool: True if Tor is active, False if Tor Jail was activated.
        """
        if self.tor_jailed:
            print("[TorGuardian] ⚠️ Tor Jail is active. Cannot proceed.")
            return False
        
        if not self.check_tor():
            print("[TorGuardian] ❌ Tor is not active. Activating Tor Jail.")
            self.activate_tor_jail()
            return False
        
        print("[TorGuardian] ✅ Tor is active. Proceeding.")
        return True

    def monitor_tor(self, interval: int = 60) -> None:
        """
        Continuously monitor Tor connectivity.
        
        Args:
            interval: Time in seconds between checks.
        """
        print(f"[TorGuardian] 🔍 Starting Tor monitor (interval: {interval}s).")
        while True:
            if not self.check_tor():
                print("[TorGuardian] ❌ Tor check failed. Activating Tor Jail.")
                self.activate_tor_jail()
                break
            time.sleep(interval)

    def is_jailed(self) -> bool:
        """
        Check if Tor Jail is active.
        
        Returns:
            bool: True if Tor Jail is active, False otherwise.
        """
        return self.tor_jailed


if __name__ == "__main__":
    # Example usage
    guardian = TorGuardian()
    if guardian.ensure_tor():
        print("Tor is active. System is secure.")
    else:
        print("Tor is not active. System is locked.")
