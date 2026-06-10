#!/usr/bin/env python3
"""
WalletManager Module
====================
Manages Bitcoin wallets (Sparrow, Wasabi, Electrum) with Tor integration.
- Supports CoinJoin for anonymity.
- Generates new addresses per transaction to avoid linking.
"""

import os
import json
import subprocess
import secrets
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path


class WalletManager:
    """
    Manages Bitcoin wallets with Tor integration.
    Supports Sparrow, Wasabi, and Electrum.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize WalletManager with configuration.
        
        Args:
            config_path: Path to settings.json. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.wallet_settings = self.config.get("wallet_settings", {})
        self.tor_proxy = self.config.get("tor_proxy", "socks5://127.0.0.1:9050")
        self.active_wallets = {}

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "wallet_settings": {
                    "sparrow": {
                        "path": "wallets/sparrow.jar",
                        "proxy_args": "--proxy socks5:127.0.0.1:9050",
                        "coinjoin_backend": "whirlpool",
                    },
                    "wasabi": {
                        "path": "wallets/Wasabi.Wallet.Wpf.dll",
                        "headless_args": "--headless --proxy socks5://127.0.0.1:9050",
                        "coinjoin_enabled": True,
                    },
                    "electrum": {
                        "path": "electrum",
                        "proxy_args": "--proxy socks5:127.0.0.1:9050",
                        "coinjoin_plugin": True,
                    },
                },
                "tor_proxy": "socks5://127.0.0.1:9050",
            }

    def start_wallet(self, wallet_name: str) -> bool:
        """
        Start a wallet with Tor proxy.
        
        Args:
            wallet_name: Name of the wallet (e.g., "sparrow", "wasabi", "electrum").
        
        Returns:
            bool: True if wallet was started successfully, False otherwise.
        """
        if wallet_name not in self.wallet_settings:
            print(f"[WalletManager] ❌ Unknown wallet: {wallet_name}")
            return False
        
        wallet_config = self.wallet_settings[wallet_name]
        wallet_path = os.path.join(os.path.dirname(__file__), "..", wallet_config["path"])
        
        if not os.path.exists(wallet_path):
            print(f"[WalletManager] ❌ Wallet path does not exist: {wallet_path}")
            return False
        
        try:
            if wallet_name == "sparrow":
                # Start Sparrow with Tor proxy
                cmd = ["java", "-jar", wallet_path, wallet_config["proxy_args"]]
                subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"[WalletManager] ✅ Started Sparrow with Tor proxy.")
            
            elif wallet_name == "wasabi":
                # Start Wasabi in headless mode with Tor proxy
                cmd = ["dotnet", wallet_path, wallet_config["headless_args"]]
                subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"[WalletManager] ✅ Started Wasabi with Tor proxy.")
            
            elif wallet_name == "electrum":
                # Start Electrum with Tor proxy
                cmd = [wallet_path, wallet_config["proxy_args"]]
                subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"[WalletManager] ✅ Started Electrum with Tor proxy.")
            
            self.active_wallets[wallet_name] = True
            return True
        except Exception as e:
            print(f"[WalletManager] ❌ Failed to start {wallet_name}: {e}")
            return False

    def stop_wallet(self, wallet_name: str) -> bool:
        """
        Stop a running wallet.
        
        Args:
            wallet_name: Name of the wallet to stop.
        
        Returns:
            bool: True if wallet was stopped successfully, False otherwise.
        """
        if wallet_name not in self.active_wallets:
            print(f"[WalletManager] ❌ Wallet not active: {wallet_name}")
            return False
        
        try:
            if wallet_name == "sparrow":
                subprocess.run(["pkill", "-f", "java -jar.*sparrow"], check=False)
            elif wallet_name == "wasabi":
                subprocess.run(["pkill", "-f", "dotnet.*Wasabi"], check=False)
            elif wallet_name == "electrum":
                subprocess.run(["pkill", "-f", "electrum"], check=False)
            
            del self.active_wallets[wallet_name]
            print(f"[WalletManager] ✅ Stopped {wallet_name}.")
            return True
        except Exception as e:
            print(f"[WalletManager] ❌ Failed to stop {wallet_name}: {e}")
            return False

    def stop_all_wallets(self) -> None:
        """Stop all running wallets."""
        for wallet_name in list(self.active_wallets.keys()):
            self.stop_wallet(wallet_name)

    def generate_address(self, wallet_name: str) -> Optional[str]:
        """
        Generate a new Bitcoin address for a wallet.
        
        Args:
            wallet_name: Name of the wallet.
        
        Returns:
            str: New Bitcoin address, or None if generation failed.
        """
        if wallet_name not in self.active_wallets:
            print(f"[WalletManager] ❌ Wallet not active: {wallet_name}")
            return None
        
        # Simulate address generation (in a real implementation, this would use wallet APIs)
        address = self._generate_random_address()
        print(f"[WalletManager] ✅ Generated new address for {wallet_name}: {address}")
        return address

    def _generate_random_address(self) -> str:
        """Generate a random Bitcoin-like address for testing."""
        # This is a placeholder. In a real implementation, use wallet APIs.
        prefix = secrets.choice(["bc1", "3", "1"])
        random_part = secrets.token_hex(15)
        return f"{prefix}{random_part}"

    def get_wallet_status(self, wallet_name: str) -> Dict[str, Any]:
        """
        Get the status of a wallet.
        
        Args:
            wallet_name: Name of the wallet.
        
        Returns:
            Dict: Wallet status (active, path, proxy, etc.).
        """
        if wallet_name not in self.wallet_settings:
            return {"error": f"Unknown wallet: {wallet_name}"}
        
        wallet_config = self.wallet_settings[wallet_name]
        return {
            "name": wallet_name,
            "active": wallet_name in self.active_wallets,
            "path": wallet_config["path"],
            "proxy_enabled": True,
            "coinjoin_enabled": wallet_config.get("coinjoin_enabled", False),
        }

    def list_wallets(self) -> List[Dict[str, Any]]:
        """
        List all configured wallets and their status.
        
        Returns:
            List: List of wallet status dictionaries.
        """
        wallets = []
        for wallet_name in self.wallet_settings:
            wallets.append(self.get_wallet_status(wallet_name))
        return wallets

    def enable_coinjoin(self, wallet_name: str) -> bool:
        """
        Enable CoinJoin for a wallet.
        
        Args:
            wallet_name: Name of the wallet.
        
        Returns:
            bool: True if CoinJoin was enabled successfully, False otherwise.
        """
        if wallet_name not in self.wallet_settings:
            print(f"[WalletManager] ❌ Unknown wallet: {wallet_name}")
            return False
        
        wallet_config = self.wallet_settings[wallet_name]
        if "coinjoin_enabled" not in wallet_config:
            print(f"[WalletManager] ❌ CoinJoin not supported for {wallet_name}.")
            return False
        
        wallet_config["coinjoin_enabled"] = True
        print(f"[WalletManager] ✅ Enabled CoinJoin for {wallet_name}.")
        return True

    def disable_coinjoin(self, wallet_name: str) -> bool:
        """
        Disable CoinJoin for a wallet.
        
        Args:
            wallet_name: Name of the wallet.
        
        Returns:
            bool: True if CoinJoin was disabled successfully, False otherwise.
        """
        if wallet_name not in self.wallet_settings:
            print(f"[WalletManager] ❌ Unknown wallet: {wallet_name}")
            return False
        
        wallet_config = self.wallet_settings[wallet_name]
        if "coinjoin_enabled" not in wallet_config:
            print(f"[WalletManager] ❌ CoinJoin not supported for {wallet_name}.")
            return False
        
        wallet_config["coinjoin_enabled"] = False
        print(f"[WalletManager] ✅ Disabled CoinJoin for {wallet_name}.")
        return True


if __name__ == "__main__":
    # Example usage
    manager = WalletManager()
    
    # List wallets
    wallets = manager.list_wallets()
    print(f"Configured wallets: {wallets}")
    
    # Start a wallet (simulated)
    manager.start_wallet("electrum")
    
    # Generate an address
    address = manager.generate_address("electrum")
    print(f"Generated address: {address}")
    
    # Stop all wallets
    manager.stop_all_wallets()
