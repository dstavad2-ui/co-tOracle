#!/usr/bin/env python3
"""
CostOracle Module
=================
Calculates costs, margins, and prices for NTRLI's products.
- Static cost data (e.g., basehash_cost_per_gram = 28 DKK).
- Dynamic pricing via AI Oracle (Devstral).
- Validates margins against NTRLI's requirements.
- Supports multiple cryptocurrencies (BTC, XMR, LTC, BCH).

NTRLI Principles:
- No Taxes: No financial reporting.
- No Traceability: No transaction logging.
- Absolute Sovereignty: User controls pricing.
"""

import os
import json
import math
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime


class CostOracle:
    """
    Calculates and validates costs, margins, and prices for NTRLI's products.
    Supports dynamic pricing via AI Oracle.
    """

    # Static cost data (DKK)
    STATIC_COSTS = {
        "basehash_cost_per_gram": 28.0,
        "extraction_yield": 0.4,
        "labor_cost_per_batch": 50.0,
        "packaging_cost_per_unit": 5.0,
        "shipping_cost": 20.0,
    }

    # Margin requirements (percentage)
    MARGIN_REQUIREMENTS = {
        "knd": 0.8588,  # 85.88% for kanalmedlemmer
        "ret": 0.70,    # 70% for retail
        "whs": 0.60,    # 60% for wholesale
    }

    # Product database
    PRODUCTS = {
        "Fedsnade": {
            "basehash_required_per_gram": 2.5,
            "category": "knd",
            "supported_currencies": ["BTC", "XMR", "LTC", "BCH"],
        },
        "Basehash": {
            "basehash_required_per_gram": 1.0,
            "category": "knd",
            "supported_currencies": ["BTC", "XMR", "LTC", "BCH"],
        },
        "HashOlie": {
            "basehash_required_per_gram": 3.0,
            "category": "ret",
            "supported_currencies": ["BTC", "XMR", "LTC", "BCH"],
        },
    }

    # Cryptocurrency conversion rates (DKK per unit)
    CRYPTO_RATES = {
        "BTC": 500000.0,
        "XMR": 2500.0,
        "LTC": 1000.0,
        "BCH": 15000.0,
    }

    # Static margins (fallback if AI fails)
    STATIC_MARGINS = {
        "BTC": 10.0,
        "XMR": 15.0,
        "LTC": 8.0,
        "BCH": 12.0
    }

    # Dynamic pricing factors
    DYNAMIC_FACTORS = {
        "BTC": 1.0,
        "XMR": 1.1,
        "LTC": 0.95,
        "BCH": 0.98,
    }

    def __init__(self, config_path: Optional[str] = None, ai_pricing_engine: Optional[Any] = None):
        """
        Initialize CostOracle with configuration.
        
        Args:
            config_path: Path to settings.json.
            ai_pricing_engine: Optional AIPricingEngine for dynamic margins.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.ai_pricing_engine = ai_pricing_engine
        self.inventory: Dict[str, float] = {}
        self.sales_log: List[Dict[str, Any]] = []
        self.dynamic_pricing_enabled = self.config.get("cost_oracle", {}).get("dynamic_pricing_enabled", True)

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    # ==================== CRYPTO RATES ====================
    def update_crypto_rates(self, new_rates: Dict[str, float]) -> None:
        """Update cryptocurrency conversion rates."""
        self.CRYPTO_RATES.update(new_rates)
        print(f"[CostOracle] 💰 Updated crypto rates: {new_rates}")

    def fetch_live_rates(self) -> Dict[str, float]:
        """Fetch live cryptocurrency rates (simulated)."""
        print("[CostOracle] 🌍 Fetching live crypto rates...")
        simulated_rates = {
            "BTC": self.CRYPTO_RATES["BTC"] * secrets.SystemRandom().uniform(0.95, 1.05),
            "XMR": self.CRYPTO_RATES["XMR"] * secrets.SystemRandom().uniform(0.95, 1.05),
            "LTC": self.CRYPTO_RATES["LTC"] * secrets.SystemRandom().uniform(0.95, 1.05),
            "BCH": self.CRYPTO_RATES["BCH"] * secrets.SystemRandom().uniform(0.95, 1.05),
        }
        self.update_crypto_rates(simulated_rates)
        return simulated_rates

    def get_crypto_rate(self, currency: str) -> float:
        """Get the current conversion rate for a cryptocurrency."""
        return self.CRYPTO_RATES.get(currency, 0.0)

    # ==================== DYNAMIC PRICING (AI) ====================
    async def calculate_margin(self, currency: str) -> float:
        """
        Calculate dynamic margin for a currency (via AI or static fallback).
        
        Args:
            currency: Cryptocurrency symbol (e.g., "BTC", "XMR").
        
        Returns:
            float: Margin percentage.
        """
        if self.dynamic_pricing_enabled and self.ai_pricing_engine:
            try:
                return await self.ai_pricing_engine.get_dynamic_margin(currency)
            except Exception as e:
                print(f"[CostOracle] ⚠️ AI pricing failed, falling back to static margin: {e}")
        return self.STATIC_MARGINS.get(currency, 10.0)

    # ==================== COST CALCULATIONS ====================
    def calculate_extract_cost(self, basehash_grams: float, currency: str = "BTC") -> float:
        """Calculate cost per gram of extract."""
        basehash_cost = basehash_grams * self.STATIC_COSTS["basehash_cost_per_gram"]
        extract_grams = basehash_grams * self.STATIC_COSTS["extraction_yield"]
        labor_cost = self.STATIC_COSTS["labor_cost_per_batch"]
        total_cost = basehash_cost + labor_cost
        cost_per_gram = total_cost / extract_grams
        
        if self.dynamic_pricing_enabled and currency in self.DYNAMIC_FACTORS:
            cost_per_gram *= self.DYNAMIC_FACTORS[currency]
        
        return round(cost_per_gram, 2)

    def calculate_product_cost(self, product_name: str, quantity: float, currency: str = "BTC") -> float:
        """Calculate total production cost for a product."""
        if product_name not in self.PRODUCTS:
            raise ValueError(f"Unknown product: {product_name}")
        
        product = self.PRODUCTS[product_name]
        basehash_required = quantity * product["basehash_required_per_gram"]
        basehash_cost = basehash_required * self.STATIC_COSTS["basehash_cost_per_gram"]
        labor_cost = self.STATIC_COSTS["labor_cost_per_batch"]
        packaging_cost = quantity * self.STATIC_COSTS["packaging_cost_per_unit"]
        total_cost = basehash_cost + labor_cost + packaging_cost
        
        if self.dynamic_pricing_enabled and currency in self.DYNAMIC_FACTORS:
            total_cost *= self.DYNAMIC_FACTORS[currency]
        
        return round(total_cost, 2)

    # ==================== MARGIN VALIDATION ====================
    def validate_margin(
        self, product_name: str, price: float, category: str, currency: str = "BTC"
    ) -> Dict[str, Any]:
        """Validate if a price meets NTRLI's margin requirements."""
        if product_name not in self.PRODUCTS:
            return {"valid": False, "error": f"Unknown product: {product_name}"}
        if category not in self.MARGIN_REQUIREMENTS:
            return {"valid": False, "error": f"Unknown category: {category}"}
        
        production_cost = self.calculate_product_cost(product_name, 1.0, currency)
        margin = (price - production_cost) / price
        required_margin = self.MARGIN_REQUIREMENTS[category]
        
        return {
            "valid": margin >= required_margin,
            "product": product_name,
            "price": price,
            "production_cost": production_cost,
            "margin": round(margin * 100, 2),
            "required_margin": round(required_margin * 100, 2),
            "category": category,
            "currency": currency,
            "currency_rate": self.get_crypto_rate(currency),
        }

    # ==================== SALES LOGGING ====================
    def log_sale(
        self,
        product_name: str,
        quantity: float,
        category: str,
        price: float,
        payment_method: str,
        currency: str = "BTC",
    ) -> Dict[str, Any]:
        """Log a sale (no permanent storage, only in-memory)."""
        if product_name not in self.PRODUCTS:
            return {"status": "error", "error": f"Unknown product: {product_name}"}
        
        product = self.PRODUCTS[product_name]
        if currency not in product.get("supported_currencies", ["BTC"]):
            return {"status": "error", "error": f"Currency {currency} not supported for {product_name}"}
        
        if product_name not in self.inventory:
            self.inventory[product_name] = 0
        self.inventory[product_name] -= quantity
        
        sale_entry = {
            "product": product_name,
            "quantity": quantity,
            "category": category,
            "price": price,
            "payment_method": payment_method,
            "currency": currency,
            "currency_rate": self.get_crypto_rate(currency),
            "timestamp": self._get_timestamp(),
            "margin": self.validate_margin(product_name, price, category, currency)["margin"],
        }
        self.sales_log.append(sale_entry)
        return {"status": "success", "sale": sale_entry}

    # ==================== DEMAND PREDICTION ====================
    def predict_demand(self, product_name: str, days: int) -> Dict[str, Any]:
        """Predict demand for a product based on historical sales."""
        if product_name not in self.PRODUCTS:
            return {"error": f"Unknown product: {product_name}"}
        
        product_sales = [sale for sale in self.sales_log if sale["product"] == product_name]
        if not product_sales:
            return {"predicted_demand": 0, "confidence": 0.0}
        
        total_quantity = sum(sale["quantity"] for sale in product_sales)
        total_days = len(set(sale["timestamp"] for sale in product_sales))
        avg_daily_sales = total_quantity / total_days if total_days > 0 else 0
        predicted_demand = avg_daily_sales * days
        
        return {
            "product": product_name,
            "predicted_demand": round(predicted_demand, 2),
            "avg_daily_sales": round(avg_daily_sales, 2),
            "confidence": min(1.0, len(product_sales) / 10.0),
        }

    # ==================== UTILITIES ====================
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def get_inventory(self) -> Dict[str, float]:
        """Get current inventory levels."""
        return self.inventory.copy()

    def update_inventory(self, product_name: str, quantity: float) -> bool:
        """Update inventory for a product."""
        if product_name not in self.PRODUCTS:
            return False
        if product_name not in self.inventory:
            self.inventory[product_name] = 0
        self.inventory[product_name] += quantity
        return True

    def enable_dynamic_pricing(self, enabled: bool = True) -> None:
        """Enable or disable dynamic pricing."""
        self.dynamic_pricing_enabled = enabled
        print(f"[CostOracle] {'✅' if enabled else '❌'} Dynamic pricing {'enabled' if enabled else 'disabled'}")

    def get_supported_currencies(self, product_name: Optional[str] = None) -> List[str]:
        """Get a list of supported cryptocurrencies."""
        if product_name and product_name in self.PRODUCTS:
            return self.PRODUCTS[product_name].get("supported_currencies", ["BTC"])
        currencies = set()
        for product in self.PRODUCTS.values():
            currencies.update(product.get("supported_currencies", ["BTC"]))
        return list(currencies)


if __name__ == "__main__":
    oracle = CostOracle()
    oracle.fetch_live_rates()
    for currency in ["BTC", "XMR", "LTC", "BCH"]:
        cost = oracle.calculate_extract_cost(5.0, currency)
        print(f"Extract cost for 5g basehash ({currency}): {cost} DKK/g")
    for currency in ["BTC", "XMR"]:
        margin = oracle.validate_margin("Fedsnade", 350, "knd", currency)
        print(f"Margin validation ({currency}): {margin}")
    sale = oracle.log_sale("Fedsnade", 1, "knd", 350, "XMR", "XMR")
    print(f"Sale log: {sale}")
