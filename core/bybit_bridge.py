#!/usr/bin/env python3
"""
BybitBridge Module
==================
Handles Bybit API requests (deposit, transactions) via Tor.
- Supports HMAC-SHA256 signing for API requests.
- Enforces rate limiting (20 requests/minute).
- Verifies deposits and transactions.
- Supports multiple cryptocurrencies (BTC, XMR, LTC, BCH).
- Integrates with AI Trading Advisor for recommendations.

NTRLI Principles:
- No Taxes: No financial reporting.
- No Traceability: All requests via Tor.
- Absolute Sovereignty: User controls transactions.
"""

import os
import json
import time
import hmac
import hashlib
import requests
import asyncio
from functools import lru_cache
from typing import Optional, Dict, Any, List


class BybitBridge:
    """
    Handles Bybit API integration with Tor support.
    Supports deposit address generation, transaction verification, and rate limiting.
    Integrates with AI Trading Advisor for trade recommendations.
    """

    SUPPORTED_COINS = ["BTC", "XMR", "LTC", "BCH", "ETH", "USDT"]

    def __init__(self, config_path: Optional[str] = None, ai_trading_advisor: Optional[Any] = None):
        """
        Initialize BybitBridge with configuration.
        
        Args:
            config_path: Path to settings.json.
            ai_trading_advisor: Optional AITradingAdvisor for trade recommendations.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.bybit_config = self.config.get("bybit_bridge", {})
        self.base_url = self.bybit_config.get("base_url", "https://api.bybit.com")
        self.rate_limit = self.bybit_config.get("api_rate_limit", 20)
        self.timeout = self.bybit_config.get("timeout", 10)
        self.tor_proxy = self.config.get("tor_guardian", {}).get("tor_proxy", "socks5://127.0.0.1:9050")
        self.api_key = None
        self.api_secret = None
        self.last_request_time = 0
        self.request_count = 0
        self.cache_enabled = True
        self.ai_trading_advisor = ai_trading_advisor

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "bybit_bridge": {
                    "base_url": "https://api.bybit.com",
                    "api_rate_limit": 20,
                    "timeout": 10,
                },
                "tor_guardian": {
                    "tor_proxy": "socks5://127.0.0.1:9050"
                }
            }

    # ==================== API CREDENTIALS ====================
    def set_api_credentials(self, api_key: str, api_secret: str) -> None:
        """Set Bybit API credentials."""
        self.api_key = api_key
        self.api_secret = api_secret
        print("[BybitBridge] ✅ API credentials set.")

    # ==================== REQUEST SIGNING ====================
    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign a request with HMAC-SHA256 for Bybit API."""
        if not self.api_secret:
            raise ValueError("API secret not set. Call set_api_credentials() first.")
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed_params = params.copy()
        signed_params["sign"] = signature
        return signed_params

    # ==================== RATE LIMITING ====================
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting (20 requests/minute)."""
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

    # ==================== REQUEST HANDLING ====================
    @lru_cache(maxsize=100)
    def _cached_make_request(
        self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, signed: bool = False
    ) -> Dict[str, Any]:
        """Cached version of _make_request."""
        return self._make_request(endpoint, method, params, signed)

    def _make_request(
        self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, signed: bool = False
    ) -> Dict[str, Any]:
        """Make a request to the Bybit API via Tor."""
        if self.cache_enabled and method == "GET":
            return self._cached_make_request(endpoint, method, params, signed)
        self._enforce_rate_limit()
        url = f"{self.base_url}{endpoint}"
        proxies = {"http": self.tor_proxy, "https": self.tor_proxy}
        headers = {"User-Agent": "NTRLI_MOBILE_AGENT"}
        if signed:
            if not self.api_key:
                raise ValueError("API key not set. Call set_api_credentials() first.")
            headers["API-KEY"] = self.api_key
            params = self._sign_request(params or {})
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=params, headers=headers, proxies=proxies, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[BybitBridge] ❌ API request failed: {e}")
            return {"error": str(e)}

    async def _async_make_request(
        self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, signed: bool = False
    ) -> Dict[str, Any]:
        """Make an async request to the Bybit API."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._make_request(endpoint, method, params, signed)
        )

    # ==================== DEPOSIT MANAGEMENT ====================
    def generate_deposit_address(self, coin: str = "BTC") -> Dict[str, Any]:
        """Generate a new deposit address for a coin."""
        if coin not in self.SUPPORTED_COINS:
            return {"error": f"Unsupported coin: {coin}. Supported: {self.SUPPORTED_COINS}"}
        endpoint = "/spot/v1/account/deposit/address"
        params = {"coin": coin}
        return self._make_request(endpoint, "POST", params, signed=True)

    def verify_deposit(self, tx_id: str) -> Dict[str, Any]:
        """Verify if a deposit transaction is completed."""
        endpoint = "/spot/v1/account/deposit/record"
        params = {"txId": tx_id}
        return self._make_request(endpoint, "GET", params, signed=True)

    def get_deposit_records(self, coin: str = "BTC", limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent deposit records for a coin."""
        if coin not in self.SUPPORTED_COINS:
            return []
        endpoint = "/spot/v1/account/deposit/record"
        params = {"coin": coin, "limit": limit}
        response = self._make_request(endpoint, "GET", params, signed=True)
        return response.get("result", [])

    # ==================== BALANCE MANAGEMENT ====================
    def get_balance(self, coin: str = "BTC") -> Dict[str, Any]:
        """Get the balance for a specific coin."""
        if coin not in self.SUPPORTED_COINS:
            return {"error": f"Unsupported coin: {coin}"}
        endpoint = "/spot/v1/account/balance"
        params = {"coin": coin}
        return self._make_request(endpoint, "GET", params, signed=True)

    def get_all_balances(self) -> Dict[str, Any]:
        """Get balances for all supported coins."""
        balances = {}
        for coin in self.SUPPORTED_COINS:
            balance = self.get_balance(coin)
            if "error" not in balance:
                balances[coin] = balance
        return balances

    # ==================== AI TRADE RECOMMENDATIONS ====================
    async def get_trade_recommendation(self, currency: str, current_price: float) -> Dict[str, Any]:
        """Get a trade recommendation from the AI Trading Advisor."""
        if not self.ai_trading_advisor:
            return {
                "currency": currency,
                "price": current_price,
                "recommendation": "HOLD",
                "confidence": 0.0,
                "error": "AI Trading Advisor not configured."
            }
        try:
            should_buy = await self.ai_trading_advisor.should_buy(currency, current_price)
            should_sell = await self.ai_trading_advisor.should_sell(currency, current_price)
            recommendation = "BUY" if should_buy else ("SELL" if should_sell else "HOLD")
            return {
                "currency": currency,
                "price": current_price,
                "recommendation": recommendation,
                "confidence": 0.9,
            }
        except Exception as e:
            return {
                "currency": currency,
                "price": current_price,
                "recommendation": "HOLD",
                "confidence": 0.0,
                "error": str(e)
            }

    # ==================== UTILITIES ====================
    def test_connectivity(self) -> bool:
        """Test connectivity to the Bybit API."""
        endpoint = "/v2/public/spot/symbols"
        response = self._make_request(endpoint, "GET")
        return "result" in response and len(response["result"]) > 0

    def enable_caching(self, enabled: bool = True) -> None:
        """Enable or disable caching for API requests."""
        self.cache_enabled = enabled
        print(f"[BybitBridge] {'✅' if enabled else '❌'} Caching {'enabled' if enabled else 'disabled'}")

    def clear_cache(self) -> None:
        """Clear the API request cache."""
        self._cached_make_request.cache_clear()
        print("[BybitBridge] 🧹 Cache cleared.")

    def get_supported_coins(self) -> List[str]:
        """Get a list of supported cryptocurrencies."""
        return self.SUPPORTED_COINS.copy()

    async def async_get_balance(self, coin: str = "BTC") -> Dict[str, Any]:
        """Asynchronously get the balance for a specific coin."""
        if coin not in self.SUPPORTED_COINS:
            return {"error": f"Unsupported coin: {coin}"}
        return await self._async_make_request("/spot/v1/account/balance", "GET", {"coin": coin}, signed=True)

    async def async_get_all_balances(self) -> Dict[str, Any]:
        """Asynchronously get balances for all supported coins."""
        tasks = [self.async_get_balance(coin) for coin in self.SUPPORTED_COINS]
        results = await asyncio.gather(*tasks)
        balances = {}
        for coin, result in zip(self.SUPPORTED_COINS, results):
            if "error" not in result:
                balances[coin] = result
        return balances


if __name__ == "__main__":
    bridge = BybitBridge()
    if bridge.test_connectivity():
        print("[BybitBridge] ✅ Connected to Bybit API.")
    else:
        print("[BybitBridge] ❌ Failed to connect to Bybit API.")
    bridge.set_api_credentials("test_api_key", "test_api_secret")
    print(f"Supported coins: {bridge.get_supported_coins()}")
