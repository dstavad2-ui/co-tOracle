#!/usr/bin/env python3
"""
NTRLICore Module
================
The heart of NTRLI_MOBILE_AGENT.
- Integrates all modules (TorGuardian, DataVault, WalletManager, BybitBridge, CostOracle).
- Implements core functions: log_sale, validate_margin, predict_demand, calculate_extract_cost.
- Supports dynamic batch processing.
- Supports multiple cryptocurrencies.
- Logging for regnskab (NO permanent transaction storage).

NTRLI Principles:
- No Taxes: No financial reporting.
- No Traceability: No transaction storage, only temporary RAM + logging for regnskab.
- Absolute Sovereignty: User controls all operations.
"""

import os
import json
import secrets
import threading
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

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
            config_path: Path to settings.json.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        
        # Initialize all modules
        self.tor_guardian = TorGuardian(self.config_path)
        self.data_vault = DataVault(self.config_path)
        self.cost_oracle = CostOracle(self.config_path)
        self.wallet_manager = WalletManager(self.config_path)
        self.bybit_bridge = BybitBridge(self.config_path)
        
        # Core state
        self.sales_batch: List[Dict[str, Any]] = []
        self.batch_threshold = self.config.get("ntrli_core", {}).get("batch_threshold", 5)
        self.dynamic_batch_threshold = self.config.get("ntrli_core", {}).get("dynamic_batch_threshold", True)
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.current_currency = self.config.get("cost_oracle", {}).get("default_currency", "BTC")
        
        # Temporary transaction storage (RAM only, cleared after retention period)
        self._temp_transactions: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = datetime.now()
        
        # Configure logging for regnskab (orders only)
        self._setup_logging()

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _setup_logging(self) -> None:
        """Set up logging for regnskab (orders only)."""
        log_config = self.config.get("ntrli_core", {}).get("logging_enabled", True)
        if not log_config:
            return
        
        log_file = self.config.get("ntrli_core", {}).get("log_file", "ntRLI_orders.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="[%(asctime)s] [NTRLI] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.logger = logging.getLogger("NTRLI")
        
        # Start cleanup thread for temporary transactions
        cleanup_thread = threading.Thread(target=self._cleanup_temp_transactions, daemon=True)
        cleanup_thread.start()

    def _cleanup_temp_transactions(self) -> None:
        """Clean up temporary transactions from RAM after retention period."""
        retention_minutes = self.config.get("ntrli_core", {}).get("temp_transaction_retention_minutes", 60)
        while True:
            if (datetime.now() - self._last_cleanup) > timedelta(minutes=retention_minutes):
                self._temp_transactions.clear()
                self._last_cleanup = datetime.now()
            threading.Event().wait(60)  # Check every 60 seconds

    # ==================== CURRENCY MANAGEMENT ====================
    def set_currency(self, currency: str) -> bool:
        """Set the default cryptocurrency for transactions."""
        supported_currencies = self.cost_oracle.get_supported_currencies()
        if currency in supported_currencies:
            self.current_currency = currency
            print(f"[NTRLICore] 💰 Set default currency to: {currency}")
            return True
        else:
            print(f"[NTRLICore] ❌ Unsupported currency: {currency}")
            return False

    # ==================== BATCH PROCESSING ====================
    def set_batch_threshold(self, threshold: int) -> None:
        """Set the batch threshold for processing sales."""
        self.batch_threshold = threshold
        print(f"[NTRLICore] 📦 Set batch threshold to: {threshold}")

    def enable_dynamic_batch_threshold(self, enabled: bool = True) -> None:
        """Enable or disable dynamic batch threshold."""
        self.dynamic_batch_threshold = enabled
        print(f"[NTRLICore] {'✅' if enabled else '❌'} Dynamic batch threshold {'enabled' if enabled else 'disabled'}")

    def _adjust_batch_threshold(self) -> None:
        """Dynamically adjust the batch threshold based on system load."""
        if not self.dynamic_batch_threshold:
            return
        active_wallets = len(self.wallet_manager.list_wallets())
        if active_wallets >= 3:
            new_threshold = 10
        elif active_wallets >= 1:
            new_threshold = 7
        else:
            new_threshold = 5
        if new_threshold != self.batch_threshold:
            self.batch_threshold = new_threshold
            print(f"[NTRLICore] 🔄 Adjusted batch threshold to: {new_threshold}")

    # ==================== SALE LOGGING (REGNSKAB) ====================
    async def log_sale(
        self,
        product_name: str,
        quantity: float,
        category: str,
        price: float,
        payment_method: str,
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log a sale for regnskab (NO permanent storage).
        Generates a new cryptocurrency address and updates inventory.
        """
        currency = currency or self.current_currency
        
        # Validate margin
        margin_result = self.cost_oracle.validate_margin(product_name, price, category, currency)
        if not margin_result["valid"]:
            return {
                "status": "error",
                "error": f"Margin too low: {margin_result['margin']}% < {margin_result['required_margin']}%",
            }
        
        # Log the sale in CostOracle
        sale_result = self.cost_oracle.log_sale(
            product_name, quantity, category, price, payment_method, currency
        )
        if sale_result["status"] != "success":
            return sale_result
        
        # Generate a new cryptocurrency address
        address = self.wallet_manager.generate_address_for_currency("electrum", currency)
        if not address:
            return {"status": "error", "error": "Failed to generate cryptocurrency address."}
        
        # Apply dynamic amount masking (±5%)
        masked_price = self._apply_amount_masking(price)
        
        # Create safe log entry (NO sensitive data)
        safe_sale_data = {
            "order_id": sale_result["sale"].get("timestamp", datetime.now().isoformat()),
            "product": product_name,
            "quantity": quantity,
            "category": category,
            "price": price,
            "currency": currency,
            "timestamp": datetime.now().isoformat(),
            "status": "LOGGED"
        }
        
        # Log to file (for regnskab)
        if hasattr(self, 'logger'):
            self.logger.info(f"Order logged: {safe_sale_data}")
        
        # Store temporarily in RAM (NO permanent storage)
        order_id = safe_sale_data["order_id"]
        self._temp_transactions[order_id] = safe_sale_data
        
        # Add to batch
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
            "currency": currency,
            "message": f"Sale logged. Use the provided {currency} address for payment.",
        }

    def _apply_amount_masking(self, amount: float) -> float:
        """Apply dynamic amount masking (±5% random variation)."""
        variation = secrets.SystemRandom().uniform(-0.05, 0.05)
        return round(amount * (1 + variation), 2)

    def _batch_process_sales(self) -> None:
        """Process all sales in the current batch."""
        if not self.sales_batch:
            return
        print(f"[NTRLICore] 📦 Processing batch of {len(self.sales_batch)} sales.")
        self._adjust_batch_threshold()
        self.sales_batch = []

    # ==================== CORE FUNCTIONS ====================
    def validate_margin(self, product_name: str, price: float, category: str, currency: Optional[str] = None) -> Dict[str, Any]:
        """Validate if a price meets NTRLI's margin requirements."""
        currency = currency or self.current_currency
        return self.cost_oracle.validate_margin(product_name, price, category, currency)

    def predict_demand(self, product_name: str, days: int) -> Dict[str, Any]:
        """Predict demand for a product."""
        return self.cost_oracle.predict_demand(product_name, days)

    def calculate_extract_cost(self, basehash_grams: float, currency: Optional[str] = None) -> float:
        """Calculate the cost per gram of extract."""
        currency = currency or self.current_currency
        return self.cost_oracle.calculate_extract_cost(basehash_grams, currency)

    # ==================== TEMPORARY TRANSACTIONS ====================
    def clear_temp_transactions(self) -> None:
        """Clear all temporary transactions from RAM."""
        self._temp_transactions.clear()
        print("[NTRLICore] 🧹 Temporary transactions cleared.")

    def get_temp_transaction(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get a temporary transaction from RAM."""
        return self._temp_transactions.get(order_id)

    # ==================== MONITORING ====================
    def monitor_system(self) -> None:
        """Start background monitoring of Tor, wallets, and transactions."""
        if self.monitoring_active:
            print("[NTRLICore] ⚠️ Monitoring already active.")
            return
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[NTRLICore] 🔍 Started system monitoring.")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        import time
        while self.monitoring_active:
            if not self.tor_guardian.check_tor():
                print("[NTRLICore] ❌ Tor is not active. Activating Tor Jail.")
                self.tor_guardian.activate_tor_jail()
                break
            wallets = self.wallet_manager.list_wallets()
            for wallet in wallets:
                if wallet["active"] and not wallet.get("proxy_enabled", False):
                    print(f"[NTRLICore] ⚠️ Wallet {wallet['name']} is active but proxy is disabled.")
            self._adjust_batch_threshold()
            if len(self.sales_batch) >= self.batch_threshold:
                self._batch_process_sales()
            time.sleep(60)

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("[NTRLICore] 🛑 Stopped system monitoring.")

    # ==================== TOR & WALLETS ====================
    def ensure_tor(self) -> bool:
        """Ensure Tor is active."""
        return self.tor_guardian.ensure_tor()

    def start_wallets(self) -> None:
        """Start all configured wallets with Tor proxy."""
        wallets = self.wallet_manager.list_wallets()
        for wallet in wallets:
            self.wallet_manager.start_wallet(wallet["name"])

    def stop_wallets(self) -> None:
        """Stop all running wallets."""
        self.wallet_manager.stop_all_wallets()

    # ==================== STATE MANAGEMENT ====================
    def save_state(self) -> bool:
        """Save the current state to the DataVault."""
        state = {
            "inventory": self.cost_oracle.get_inventory(),
            "sales_log": self.cost_oracle.sales_log,
            "sales_batch": self.sales_batch,
            "current_currency": self.current_currency,
            "batch_threshold": self.batch_threshold,
        }
        return self.data_vault.save_data(state, confirm=False)

    def load_state(self) -> bool:
        """Load the state from the DataVault."""
        state = self.data_vault.load_data()
        if not state:
            return False
        for product, quantity in state.get("inventory", {}).items():
            self.cost_oracle.inventory[product] = quantity
        self.cost_oracle.sales_log = state.get("sales_log", [])
        self.sales_batch = state.get("sales_batch", [])
        if "current_currency" in state:
            self.current_currency = state["current_currency"]
        if "batch_threshold" in state:
            self.batch_threshold = state["batch_threshold"]
        print("[NTRLICore] ✅ State loaded from DataVault.")
        return True

    # ==================== SYSTEM WIPE ====================
    def wipe_system(self) -> None:
        """Securely wipe all system data."""
        print("[NTRLICore] 🧹 Wiping system data...")
        self.data_vault.wipe_vault()
        self.data_vault.wipe_key()
        self.stop_wallets()
        self.clear_temp_transactions()
        print("[NTRLICore] ✅ System data wiped.")

    # ==================== ASYNC SUPPORT ====================
    async def async_process_batch(self) -> None:
        """Asynchronously process the current sales batch."""
        if not self.sales_batch:
            return
        await asyncio.sleep(0.1)
        self._batch_process_sales()


if __name__ == "__main__":
    import asyncio
    core = NTRLICore()
    core.set_currency("XMR")
    core.enable_dynamic_batch_threshold(True)
    if core.ensure_tor():
        print("Tor is active. System is secure.")
    else:
        print("Tor is not active. System is locked.")
    sale_result = asyncio.run(core.log_sale(
        product_name="Fedsnade", quantity=1, category="knd", price=350, payment_method="XMR", currency="XMR"
    ))
    print(f"Sale result: {sale_result}")
    margin_result = core.validate_margin("Fedsnade", 350, "knd", "LTC")
    print(f"Margin validation (LTC): {margin_result}")
    demand_result = core.predict_demand("Fedsnade", 7)
    print(f"Demand prediction: {demand_result}")
    core.monitor_system()
    core.save_state()
    import time
    time.sleep(10)
    core.stop_monitoring()
