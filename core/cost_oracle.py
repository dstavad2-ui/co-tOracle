#!/usr/bin/env python3
"""
CostOracle Module
=================
Calculates costs, margins, and prices for NTRLI's products.
- Uses static data (e.g., basehash_cost_per_gram = 28 DKK).
- Validates margins against NTRLI's requirements.
- Predicts demand based on historical sales data.
"""

import os
import json
import math
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class CostOracle:
    """
    Calculates and validates costs, margins, and prices for NTRLI's products.
    """

    # Static cost data (DKK)
    STATIC_COSTS = {
        "basehash_cost_per_gram": 28.0,  # DKK per gram
        "extraction_yield": 0.4,         # 40% yield (5g basehash -> 2g extract)
        "labor_cost_per_batch": 50.0,    # DKK per batch
        "packaging_cost_per_unit": 5.0,  # DKK per unit
        "shipping_cost": 20.0,           # DKK per shipment
    }

    # Margin requirements (percentage)
    MARGIN_REQUIREMENTS = {
        "knd": 0.8588,  # 85.88% for kanalmedlemmer (channel members)
        "ret": 0.70,    # 70% for retail
        "whs": 0.60,    # 60% for wholesale
    }

    # Product database
    PRODUCTS = {
        "Fedsnade": {
            "basehash_required_per_gram": 2.5,  # 2.5g basehash -> 1g Fedsnade
            "category": "knd",
        },
        "Basehash": {
            "basehash_required_per_gram": 1.0,   # 1g basehash -> 1g Basehash
            "category": "knd",
        },
        "HashOlie": {
            "basehash_required_per_gram": 3.0,   # 3g basehash -> 1g HashOlie
            "category": "ret",
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize CostOracle with configuration.
        
        Args:
            config_path: Path to settings.json. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.inventory = {}
        self.sales_log = []

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def calculate_extract_cost(self, basehash_grams: float) -> float:
        """
        Calculate the cost per gram of extract based on basehash input.
        
        Args:
            basehash_grams: Amount of basehash in grams.
        
        Returns:
            float: Cost per gram of extract in DKK.
        """
        basehash_cost = basehash_grams * self.STATIC_COSTS["basehash_cost_per_gram"]
        extract_grams = basehash_grams * self.STATIC_COSTS["extraction_yield"]
        labor_cost = self.STATIC_COSTS["labor_cost_per_batch"]
        total_cost = basehash_cost + labor_cost
        cost_per_gram = total_cost / extract_grams
        return round(cost_per_gram, 2)

    def calculate_product_cost(self, product_name: str, quantity: float) -> float:
        """
        Calculate the total cost for producing a specific product.
        
        Args:
            product_name: Name of the product (e.g., "Fedsnade").
            quantity: Quantity in grams.
        
        Returns:
            float: Total production cost in DKK.
        """
        if product_name not in self.PRODUCTS:
            raise ValueError(f"Unknown product: {product_name}")
        
        product = self.PRODUCTS[product_name]
        basehash_required = quantity * product["basehash_required_per_gram"]
        basehash_cost = basehash_required * self.STATIC_COSTS["basehash_cost_per_gram"]
        labor_cost = self.STATIC_COSTS["labor_cost_per_batch"]
        packaging_cost = quantity * self.STATIC_COSTS["packaging_cost_per_unit"]
        total_cost = basehash_cost + labor_cost + packaging_cost
        return round(total_cost, 2)

    def validate_margin(self, product_name: str, price: float, category: str) -> Dict[str, Any]:
        """
        Validate if a price meets NTRLI's margin requirements.
        
        Args:
            product_name: Name of the product.
            price: Selling price in DKK.
            category: Customer category (e.g., "knd", "ret", "whs").
        
        Returns:
            Dict: Validation result with details.
        """
        if product_name not in self.PRODUCTS:
            return {"valid": False, "error": f"Unknown product: {product_name}"}
        
        if category not in self.MARGIN_REQUIREMENTS:
            return {"valid": False, "error": f"Unknown category: {category}"}
        
        # Calculate production cost (assume 1 gram for simplicity)
        production_cost = self.calculate_product_cost(product_name, 1.0)
        
        # Calculate margin
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
        }

    def log_sale(
        self,
        product_name: str,
        quantity: float,
        category: str,
        price: float,
        payment_method: str,
    ) -> Dict[str, Any]:
        """
        Log a sale and update inventory.
        
        Args:
            product_name: Name of the product.
            quantity: Quantity sold in grams.
            category: Customer category.
            price: Selling price in DKK.
            payment_method: Payment method (e.g., "XMR", "BTC", "Cash").
        
        Returns:
            Dict: Sale log entry.
        """
        if product_name not in self.PRODUCTS:
            return {"status": "error", "error": f"Unknown product: {product_name}"}
        
        # Update inventory
        if product_name not in self.inventory:
            self.inventory[product_name] = 0
        self.inventory[product_name] -= quantity
        
        # Create sale entry
        sale_entry = {
            "product": product_name,
            "quantity": quantity,
            "category": category,
            "price": price,
            "payment_method": payment_method,
            "timestamp": self._get_timestamp(),
            "margin": self.validate_margin(product_name, price, category)["margin"],
        }
        self.sales_log.append(sale_entry)
        
        return {"status": "success", "sale": sale_entry}

    def predict_demand(self, product_name: str, days: int) -> Dict[str, Any]:
        """
        Predict demand for a product based on historical sales data.
        
        Args:
            product_name: Name of the product.
            days: Number of days to predict for.
        
        Returns:
            Dict: Predicted demand.
        """
        if product_name not in self.PRODUCTS:
            return {"error": f"Unknown product: {product_name}"}
        
        # Filter sales log for the product
        product_sales = [
            sale for sale in self.sales_log if sale["product"] == product_name
        ]
        
        if not product_sales:
            return {"predicted_demand": 0, "confidence": 0.0}
        
        # Calculate average daily sales
        total_quantity = sum(sale["quantity"] for sale in product_sales)
        total_days = len(set(sale["timestamp"] for sale in product_sales))
        avg_daily_sales = total_quantity / total_days if total_days > 0 else 0
        
        predicted_demand = avg_daily_sales * days
        
        return {
            "product": product_name,
            "predicted_demand": round(predicted_demand, 2),
            "avg_daily_sales": round(avg_daily_sales, 2),
            "confidence": min(1.0, len(product_sales) / 10.0),  # Confidence increases with more data
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_inventory(self) -> Dict[str, float]:
        """
        Get current inventory levels.
        
        Returns:
            Dict: Inventory levels for all products.
        """
        return self.inventory.copy()

    def update_inventory(self, product_name: str, quantity: float) -> bool:
        """
        Update inventory for a product.
        
        Args:
            product_name: Name of the product.
            quantity: Quantity to add (positive) or remove (negative).
        
        Returns:
            bool: True if update was successful, False otherwise.
        """
        if product_name not in self.PRODUCTS:
            return False
        
        if product_name not in self.inventory:
            self.inventory[product_name] = 0
        
        self.inventory[product_name] += quantity
        return True


if __name__ == "__main__":
    # Example usage
    oracle = CostOracle()
    
    # Calculate extract cost
    extract_cost = oracle.calculate_extract_cost(5.0)
    print(f"Extract cost for 5g basehash: {extract_cost} DKK/g")
    
    # Validate margin
    margin_result = oracle.validate_margin("Fedsnade", 350, "knd")
    print(f"Margin validation: {margin_result}")
    
    # Log a sale
    sale_result = oracle.log_sale("Fedsnade", 1, "knd", 350, "XMR")
    print(f"Sale log: {sale_result}")
    
    # Predict demand
    demand_result = oracle.predict_demand("Fedsnade", 7)
    print(f"Demand prediction: {demand_result}")
