#!/usr/bin/env python3
"""
NTRLI_MOBILE_AGENT CLI
======================
Command-line interface for NTRLI_MOBILE_AGENT.
Supports CMD: commands (e.g., CMD:PROTECTOR, CMD:Do, CMD:SETUP).
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ntrli_core import NTRLICore
from core.tor_guardian import TorGuardian
from core.data_vault import DataVault
from core.cost_oracle import CostOracle
from core.wallet_manager import WalletManager
from core.bybit_bridge import BybitBridge


class NTRLI_CLI:
    """
    Command-line interface for NTRLI_MOBILE_AGENT.
    Handles CMD: commands and integrates all modules.
    """

    def __init__(self):
        """Initialize the CLI with all modules."""
        self.core = NTRLICore()
        self.tor_guardian = self.core.tor_guardian
        self.data_vault = self.core.data_vault
        self.cost_oracle = self.core.cost_oracle
        self.wallet_manager = self.core.wallet_manager
        self.bybit_bridge = self.core.bybit_bridge

    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        Parse a CMD: command.
        
        Args:
            command: The command string (e.g., "CMD:PROTECTOR").
        
        Returns:
            Dict: Parsed command with action and arguments.
        """
        if not command.startswith("CMD:"):
            return {"error": "Invalid command format. Use CMD:<action>"}
        
        parts = command.split(":", 1)
        action = parts[1].upper() if len(parts) > 1 else ""
        
        return {
            "action": action,
            "args": [],
        }

    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a CMD: command.
        
        Args:
            command: The command string.
        
        Returns:
            Dict: Result of the command execution.
        """
        parsed = self.parse_command(command)
        if "error" in parsed:
            return parsed
        
        action = parsed["action"]
        
        # Handle CMD:PROTECTOR
        if action == "PROTECTOR":
            return self._handle_protector()
        
        # Handle CMD:Do
        elif action == "DO":
            return self._handle_do()
        
        # Handle CMD:SETUP
        elif action == "SETUP":
            return self._handle_setup()
        
        # Handle CMD:START
        elif action == "START":
            return self._handle_start()
        
        # Handle CMD:STOP
        elif action == "STOP":
            return self._handle_stop()
        
        # Handle CMD:TEST
        elif action == "TEST":
            return self._handle_test()
        
        # Handle CMD:WIPE
        elif action == "WIPE":
            return self._handle_wipe()
        
        # Handle CMD:MONITOR
        elif action == "MONITOR":
            return self._handle_monitor()
        
        # Handle CMD:SALE
        elif action == "SALE":
            return self._handle_sale()
        
        # Handle CMD:MARGIN
        elif action == "MARGIN":
            return self._handle_margin()
        
        # Handle CMD:DEMAND
        elif action == "DEMAND":
            return self._handle_demand()
        
        else:
            return {"error": f"Unknown command: {action}"}

    def _handle_protector(self) -> Dict[str, Any]:
        """
        Handle CMD:PROTECTOR command.
        Activates TorGuardian to ensure Tor is active and blocks clearnet if not.
        """
        print("[CLI] 🛡️ Executing CMD:PROTECTOR...")
        
        # Ensure Tor is active
        if not self.tor_guardian.ensure_tor():
            return {
                "status": "error",
                "message": "Tor is not active. Tor Jail activated.",
            }
        
        # Start monitoring Tor
        self.tor_guardian.monitor_tor(interval=60)
        
        return {
            "status": "success",
            "message": "TorGuardian activated. All traffic is routed through Tor.",
        }

    def _handle_do(self) -> Dict[str, Any]:
        """
        Handle CMD:Do command.
        Confirms actions (e.g., saving data to DataVault).
        """
        print("[CLI] ✅ Executing CMD:Do...")
        
        # Example: Save state to DataVault
        if self.core.save_state():
            return {
                "status": "success",
                "message": "State saved to DataVault.",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to save state.",
            }

    def _handle_setup(self) -> Dict[str, Any]:
        """
        Handle CMD:SETUP command.
        Sets up the system (creates directories, initializes modules).
        """
        print("[CLI] 🛠️ Executing CMD:SETUP...")
        
        # Initialize all modules
        self.core.ensure_tor()
        self.core.load_state()
        
        return {
            "status": "success",
            "message": "System setup complete.",
        }

    def _handle_start(self) -> Dict[str, Any]:
        """
        Handle CMD:START command.
        Starts all wallets and monitoring.
        """
        print("[CLI] ▶️ Executing CMD:START...")
        
        # Start wallets
        self.core.start_wallets()
        
        # Start monitoring
        self.core.monitor_system()
        
        return {
            "status": "success",
            "message": "Wallets and monitoring started.",
        }

    def _handle_stop(self) -> Dict[str, Any]:
        """
        Handle CMD:STOP command.
        Stops all wallets and monitoring.
        """
        print("[CLI] ⏹️ Executing CMD:STOP...")
        
        # Stop monitoring
        self.core.stop_monitoring()
        
        # Stop wallets
        self.core.stop_wallets()
        
        return {
            "status": "success",
            "message": "Wallets and monitoring stopped.",
        }

    def _handle_test(self) -> Dict[str, Any]:
        """
        Handle CMD:TEST command.
        Tests all modules (Tor, DataVault, CostOracle, etc.).
        """
        print("[CLI] 🧪 Executing CMD:TEST...")
        
        results = {}
        
        # Test TorGuardian
        results["tor_guardian"] = {
            "status": "success" if self.tor_guardian.check_tor() else "error",
            "message": "Tor is active" if self.tor_guardian.check_tor() else "Tor is not active",
        }
        
        # Test DataVault
        test_data = {"test": "data"}
        if self.data_vault.save_data(test_data, confirm=False):
            loaded_data = self.data_vault.load_data()
            results["data_vault"] = {
                "status": "success" if loaded_data == test_data else "error",
                "message": "DataVault read/write test passed" if loaded_data == test_data else "DataVault test failed",
            }
            self.data_vault.wipe_vault()  # Clean up
        else:
            results["data_vault"] = {"status": "error", "message": "Failed to save test data"}
        
        # Test CostOracle
        extract_cost = self.cost_oracle.calculate_extract_cost(5.0)
        results["cost_oracle"] = {
            "status": "success",
            "message": f"Extract cost for 5g basehash: {extract_cost} DKK/g",
        }
        
        # Test WalletManager
        wallets = self.wallet_manager.list_wallets()
        results["wallet_manager"] = {
            "status": "success",
            "message": f"Configured wallets: {[w['name'] for w in wallets]}",
        }
        
        # Test BybitBridge
        if self.bybit_bridge.test_connectivity():
            results["bybit_bridge"] = {
                "status": "success",
                "message": "Bybit API connectivity test passed",
            }
        else:
            results["bybit_bridge"] = {
                "status": "error",
                "message": "Bybit API connectivity test failed",
            }
        
        return {
            "status": "success",
            "results": results,
        }

    def _handle_wipe(self) -> Dict[str, Any]:
        """
        Handle CMD:WIPE command.
        Securely wipes all system data.
        """
        print("[CLI] 🧹 Executing CMD:WIPE...")
        self.core.wipe_system()
        return {
            "status": "success",
            "message": "All system data wiped securely.",
        }

    def _handle_monitor(self) -> Dict[str, Any]:
        """
        Handle CMD:MONITOR command.
        Starts or stops system monitoring.
        """
        print("[CLI] 🔍 Executing CMD:MONITOR...")
        
        if self.core.monitoring_active:
            self.core.stop_monitoring()
            return {
                "status": "success",
                "message": "System monitoring stopped.",
            }
        else:
            self.core.monitor_system()
            return {
                "status": "success",
                "message": "System monitoring started.",
            }

    def _handle_sale(self) -> Dict[str, Any]:
        """
        Handle CMD:SALE command.
        Logs a sale (requires additional arguments).
        """
        print("[CLI] 💰 Executing CMD:SALE...")
        
        # Example sale
        sale_result = self.core.log_sale(
            product_name="Fedsnade",
            quantity=1,
            category="knd",
            price=350,
            payment_method="XMR",
        )
        return sale_result

    def _handle_margin(self) -> Dict[str, Any]:
        """
        Handle CMD:MARGIN command.
        Validates a margin (requires additional arguments).
        """
        print("[CLI] 📊 Executing CMD:MARGIN...")
        
        # Example margin validation
        margin_result = self.core.validate_margin("Fedsnade", 350, "knd")
        return margin_result

    def _handle_demand(self) -> Dict[str, Any]:
        """
        Handle CMD:DEMAND command.
        Predicts demand (requires additional arguments).
        """
        print("[CLI] 📈 Executing CMD:DEMAND...")
        
        # Example demand prediction
        demand_result = self.core.predict_demand("Fedsnade", 7)
        return demand_result

    def run_interactive(self):
        """Run the CLI in interactive mode."""
        print("""
=====================================
NTRLI_MOBILE_AGENT CLI
=====================================
Type CMD:<action> to execute a command.
Available commands:
- CMD:PROTECTOR: Activate TorGuardian
- CMD:Do: Confirm actions (e.g., save data)
- CMD:SETUP: Initialize the system
- CMD:START: Start wallets and monitoring
- CMD:STOP: Stop wallets and monitoring
- CMD:TEST: Test all modules
- CMD:WIPE: Securely wipe all data
- CMD:MONITOR: Toggle system monitoring
- CMD:SALE: Log a sale
- CMD:MARGIN: Validate a margin
- CMD:DEMAND: Predict demand
- exit: Exit the CLI
=====================================
""")
        
        while True:
            try:
                command = input("[NTRLI] > ").strip()
                if command.lower() == "exit":
                    break
                
                if command.startswith("CMD:"):
                    result = self.execute_command(command)
                    print(json.dumps(result, indent=2))
                else:
                    print("Error: Unknown command. Use CMD:<action> or 'exit'.")
            except KeyboardInterrupt:
                print("\n[NTRLI] Exiting...")
                break
            except Exception as e:
                print(f"[NTRLI] ❌ Error: {e}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="NTRLI_MOBILE_AGENT CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="CMD: command to execute (e.g., CMD:PROTECTOR)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    
    args = parser.parse_args()
    cli = NTRLI_CLI()
    
    if args.interactive or not args.command:
        cli.run_interactive()
    else:
        result = cli.execute_command(args.command)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
