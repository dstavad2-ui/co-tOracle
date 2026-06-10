#!/usr/bin/env python3
"""
BybitBridge Module
==================
Handles Bybit API requests (deposit, transactions) via Tor.
- Supports HMAC-SHA256 signing for API requests.
- Enforces rate limiting (20 requests/minute).
- Verifies deposits and transactions.
"""

import os
import json
import time
import hmac
import hashlib
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path


class BybitBridge:
    """
    Handles Bybit API integration with Tor support.
    Supports deposit address generation, transaction verification, and rate limiting.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize BybitBridge with configuration.
        
        Args:
            config_path: Path to settings.json. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.bybit_config = self.config.get("bybit_api", {})
        self.base_url = self.bybit_config.get("base_url", "https://api.bybit.com")
        self.rate_limit = self.bybit_config.get("rate_limit", 20)
        self.timeout = self.bybit_config.get("timeout", 10)
        self.tor_proxy = self.config.get("tor_proxy", "socks5://127.0.0.1:9050")
        self.api_key = None
        self.api_secret = None
        self.last_request_time = 0
        self.request_count = 0

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "bybit_api": {
                    "base_url": "https://api.bybit.com",
                    "rate_limit": 20,
                    "timeout": 10,
                },
                "tor_proxy": "socks5://127.0.0.1:9050",
            }

    def set_api_credentials(self, api_key: str, api_secret: str) -> None:
        """
        Set Bybit API credentials.
        
        Args:
            api_key: Bybit API key.
            api_secret: Bybit API secret.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        print("[BybitBridge] ✅ API credentials set.")

    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a request with HMAC-SHA256 for Bybit API.
        
        Args:
            params: Request parameters.
        
        Returns:
            Dict: Signed parameters with 'sign' field.
        """
        if not self.api_secret:
            raise ValueError("API secret not set. Call set_api_credentials() first.")
        
        # Sort parameters alphabetically
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        
        # Generate signature
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        
        signed_params = params.copy()
        signed_params["sign"] = signature
        return signed_params

    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting (20 requests/minute).
        Raises an exception if the limit is exceeded.
        """
        current_time = time.time()
        time_elapsed = current_time - self.last_request_time
        
        if time_elapsed < 60:
            if self.request_count >= self.rate_limit:
                raise Exception(
                    f"Rate limit exceeded: {self.rate_limit} requests/minute. "
                    f"Wait {60 - time_elapsed:.2f} seconds."
                )
        else:
            self.request_count = 0
            self.last_request_time = current_time
        
        self.request_count += 1

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Make a request to the Bybit API.
        
        Args:
            endpoint: API endpoint (e.g., "/v2/public/spot/symbols").
            method: HTTP method (GET, POST, etc.).
            params: Request parameters.
            signed: Whether to sign the request (for private endpoints).
        
        Returns:
            Dict: API response.
        """
        self._enforce_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        proxies = {
            "http": self.tor_proxy,
            "https": self.tor_proxy,
        }
        
        headers = {
            "User-Agent": "NTRLI_MOBILE_AGENT",
        }
        
        if signed:
            if not self.api_key:
                raise ValueError("API key not set. Call set_api_credentials() first.")
            headers["API-KEY"] = self.api_key
            params = self._sign_request(params or {})
        
        try:
            if method == "GET":
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=self.timeout,
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    json=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=self.timeout,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[BybitBridge] ❌ API request failed: {e}")
            return {"error": str(e)}

    def generate_deposit_address(self, coin: str = "BTC") -> Dict[str, Any]:
        """
        Generate a new deposit address for a coin (e.g., BTC).
        
        Args:
            coin: Coin symbol (e.g., "BTC", "XMR").
        
        Returns:
            Dict: Deposit address information.
        """
        endpoint = "/spot/v1/account/deposit/address"
        params = {
            "coin": coin,
        }
        return self._make_request(endpoint, "POST", params, signed=True)

    def verify_deposit(self, tx_id: str) -> Dict[str, Any]:
        """
        Verify if a deposit transaction is completed.
        
        Args:
            tx_id: Transaction ID to verify.
        
        Returns:
            Dict: Transaction verification result.
        """
        endpoint = "/spot/v1/account/deposit/record"
        params = {
            "txId": tx_id,
        }
        return self._make_request(endpoint, "GET", params, signed=True)

    def get_deposit_records(self, coin: str = "BTC", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent deposit records for a coin.
        
        Args:
            coin: Coin symbol (e.g., "BTC").
            limit: Maximum number of records to return.
        
        Returns:
            List: List of deposit records.
        """
        endpoint = "/spot/v1/account/deposit/record"
        params = {
            "coin": coin,
            "limit": limit,
        }
        response = self._make_request(endpoint, "GET", params, signed=True)
        return response.get("result", [])

    def get_balance(self, coin: str = "BTC") -> Dict[str, Any]:
        """
        Get the balance for a specific coin.
        
        Args:
            coin: Coin symbol (e.g., "BTC").
        
        Returns:
            Dict: Balance information.
        """
        endpoint = "/spot/v1/account/balance"
        params = {
            "coin": coin,
        }
        return self._make_request(endpoint, "GET", params, signed=True)

    def test_connectivity(self) -> bool:
        """
        Test connectivity to the Bybit API.
        
        Returns:
            bool: True if connectivity test passed, False otherwise.
        """
        endpoint = "/v2/public/spot/symbols"
        response = self._make_request(endpoint, "GET")
        return "result" in response and len(response["result"]) > 0


if __name__ == "__main__":
    # Example usage
    bridge = BybitBridge()
    
    # Test connectivity
    if bridge.test_connectivity():
        print("[BybitBridge] ✅ Connected to Bybit API.")
    else:
        print("[BybitBridge] ❌ Failed to connect to Bybit API.")
    
    # Set API credentials (example)
    bridge.set_api_credentials("test_api_key", "test_api_secret")
    
    # Generate a deposit address (requires valid API credentials)
    # address = bridge.generate_deposit_address("BTC")
    # print(f"Deposit address: {address}")
