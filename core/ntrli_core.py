#!/usr/bin/env python3
"""
NTRLICore Module
================
The heart of NTRLI_MOBILE_AGENT.
Integrates all modules (TorGuardian, DataVault, WalletManager, BybitBridge, CostOracle).
Implements core functions: log_sale, validate_margin, predict_demand, calculate_extract_cost.
"""

import os
import json
import secrets
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from .tor_guardian import TorGuardian
from .data_vault import DataVault
from .cost_oracle import CostOracle
from .wallet_manager import WalletManager
from .bybit_bridge import BybitBridge


class NTRLICore:
    """
    The core kernel of NTRLI_MOBILE_AGENT.
    Integrates all modules and implements high-level functions.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize NTRLICore with all modules.
        
        Args:
            config_path: Path to settings.json. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        
        # Initialize all modules
        self.tor_guardian = TorGuardian(self.config_path)
        self.data_vault = DataVault(self.config_path)
        self.cost_oracle = CostOracle(self.config_path)
        self.wallet_manager = WalletManager(self.config_path)
        self.bybit_bridge = BybitBridge(self.config_path)
        
        # Core state
        self.sales_batch = []
        self.batch_threshold = 5  # Process batch after 5 sales
        self.monitoring_active = False
        self.monitor_thread = None

    def log_sale(
        self,
        product_name: str,
        quantity: float,
        category: str,
        price: float,
        payment_method: str,
    ) -> Dict[str, Any]:
        """
        Log a sale, generate a new Bitcoin address, and update inventory.
        
        Args:
            product_name: Name of the product (e.g., "Fedsnade").
            quantity: Quantity sold in grams.
            category: Customer category (e.g., "knd", "ret", "whs").
            price: Selling price in DKK.
            payment_method: Payment method (e.g., "XMR", "BTC", "Cash").
        
        Returns:
            Dict: Sale result with address and status.
        """
        # Validate margin first
        margin_result = self.cost_oracle.validate_margin(product_name, price, category)
        if not margin_result["valid"]:
            return {
                "status": "error",
                "error": f"Margin too low: {margin_result['margin']}% < {margin_result['required_margin']}%",
            }
        
        # Log the sale in CostOracle
        sale_result = self.cost_oracle.log_sale(
            product_name, quantity, category, price, payment_method
        )
        if sale_result["status"] != "success":
            return sale_result
        
        # Generate a new Bitcoin address for payment
        address = self.wallet_manager.generate_address("electrum")
        if not address:
            return {"status": "error", "error": "Failed to generate Bitcoin address."}
        
        # Apply dynamic amount masking (±5% random variation)
        masked_price = self._apply_amount_masking(price)
        
        # Add to batch for later processing
        self.sales_batch.append({
            **sale_result["sale"],
            "address": address,
            "masked_price": masked_price,
        })
        
        # Process batch if threshold reached
        if len(self.sales_batch) >= self.batch_threshold:
            self._batch_process_sales()
        
        return {
            "status": "success",
            "sale": sale_result["sale"],
            "address": address,
            "masked_price": masked_price,
            "message": "Sale logged. Use the provided address for payment.",
        }

    def validate_margin(self, product_name: str, price: float, category: str) -> Dict[str, Any]:
        """
        Validate if a price meets NTRLI's margin requirements.
        
        Args:
            product_name: Name of the product.
            price: Selling price in DKK.
            category: Customer category.
        
        Returns:
            Dict: Margin validation result.
        """
        return self.cost_oracle.validate_margin(product_name, price, category)

    def predict_demand(self, product_name: str, days: int) -> Dict[str, Any]:
        """
        Predict demand for a product based on historical sales data.
        
        Args:
            product_name: Name of the product.
            days: Number of days to predict for.
        
        Returns:
            Dict: Predicted demand.
        """
        return self.cost_oracle.predict_demand(product_name, days)

    def calculate_extract_cost(self, basehash_grams: float) -> float:
        """
        Calculate the cost per gram of extract based on basehash input.
        
        Args:
            basehash_grams: Amount of basehash in grams.
        
        Returns:
            float: Cost per gram of extract in DKK.
        """
        return self.cost_oracle.calculate_extract_cost(basehash_grams)

    def _apply_amount_masking(self, amount: float) -> float:
        """
        Apply dynamic amount masking (±5% random variation).
        
        Args:
            amount: Original amount.
        
        Returns:
            float: Masked amount.
        """
        variation = secrets.SystemRandom().uniform(-0.05, 0.05)
        masked_amount = amount * (1 + variation)
        return round(masked_amount, 2)

    def _batch_process_sales(self) -> None:
        """
        Process all sales in the current batch.
        - Generates a single transaction for multiple sales.
        - Reduces fees by batching.
        """
        if not self.sales_batch:
            return
        
        print(f"[NTRLICore] 📦 Processing batch of {len(self.sales_batch)} sales.")
        
        # In a real implementation, this would:
        # 1. Generate a single transaction for all sales in the batch.
        # 2. Send the transaction via a wallet.
        # 3. Verify the transaction on Bybit.
        
        # For now, just clear the batch
        self.sales_batch = []

    def monitor_system(self) -> None:
        """
        Start background monitoring of Tor, wallets, and transactions.
        """
        if self.monitoring_active:
            print("[NTRLICore] ⚠️ Monitoring already active.")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[NTRLICore] 🔍 Started system monitoring.")

    def _monitor_loop(self) -> None:
        """
        Background monitoring loop.
        - Checks Tor connectivity.
        - Monitors wallet status.
        - Processes sales batches.
        """
        while self.monitoring_active:
            # Check Tor
            if not self.tor_guardian.check_tor():
                print("[NTRLICore] ❌ Tor is not active. Activating Tor Jail.")
                self.tor_guardian.activate_tor_jail()
                break
            
            # Check wallets
            wallets = self.wallet_manager.list_wallets()
            for wallet in wallets:
                if wallet["active"] and not wallet.get("proxy_enabled", False):
                    print(f"[NTRLICore] ⚠️ Wallet {wallet['name']} is active but proxy is disabled.")
            
            # Process batch if needed
            if len(self.sales_batch) >= self.batch_threshold:
                self._batch_process_sales()
            
            # Sleep for 60 seconds
            import time
            time.sleep(60)

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[NTRLICore] 🛑 Stopped system monitoring.")

    def ensure_tor(self) -> bool:
        """
        Ensure Tor is active before allowing external requests.
        
        Returns:
            bool: True if Tor is active, False otherwise.
        """
        return self.tor_guardian.ensure_tor()

    def start_wallets(self) -> None:
        """Start all configured wallets with Tor proxy."""
        wallets = self.wallet_manager.list_wallets()
        for wallet in wallets:
            self.wallet_manager.start_wallet(wallet["name"])

    def stop_wallets(self) -> None:
        """Stop all running wallets."""
        self.wallet_manager.stop_all_wallets()

    def save_state(self) -> bool:
        """
        Save the current state (inventory, sales log) to the DataVault.
        
        Returns:
            bool: True if state was saved successfully, False otherwise.
        """
        state = {
            "inventory": self.cost_oracle.get_inventory(),
            "sales_log": self.cost_oracle.sales_log,
            "sales_batch": self.sales_batch,
        }
        return self.data_vault.save_data(state, confirm=False)

    def load_state(self) -> bool:
        """
        Load the state (inventory, sales log) from the DataVault.
        
        Returns:
            bool: True if state was loaded successfully, False otherwise.
        """
        state = self.data_vault.load_data()
        if not state:
            return False
        
        # Restore inventory
        for product, quantity in state.get("inventory", {}).items():
            self.cost_oracle.inventory[product] = quantity
        
        # Restore sales log
        self.cost_oracle.sales_log = state.get("sales_log", [])
        
        # Restore sales batch
        self.sales_batch = state.get("sales_batch", [])
        
        print("[NTRLICore] ✅ State loaded from DataVault.")
        return True

    def wipe_system(self) -> None:
        """
        Securely wipe all system data.
        - Wipes DataVault.
        - Wipes encryption key.
        - Stops all wallets.
        """
        print("[NTRLICore] 🧹 Wiping system data...")
        self.data_vault.wipe_vault()
        self.data_vault.wipe_key()
        self.stop_wallets()
        print("[NTRLICore] ✅ System data wiped.")


if __name__ == "__main__":
    # Example usage
    core = NTRLICore()
    
    # Ensure Tor is active
    if core.ensure_tor():
        print("Tor is active. System is secure.")
    else:
        print("Tor is not active. System is locked.")
    
    # Log a sale
    sale_result = core.log_sale("Fedsnade", 1, "knd", 350, "XMR")
    print(f"Sale result: {sale_result}")
    
    # Validate margin
    margin_result = core.validate_margin("Fedsnade", 350, "knd")
    print(f"Margin validation: {margin_result}")
    
    # Predict demand
    demand_result = core.predict_demand("Fedsnade", 7)
    print(f"Demand prediction: {demand_result}")
    
    # Start monitoring
    core.monitor_system()
    
    # Save state
    core.save_state()
    
    # Stop monitoring (after some time)
    import time
    time.sleep(10)
    core.stop_monitoring()
