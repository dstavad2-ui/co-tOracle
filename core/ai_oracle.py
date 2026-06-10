#!/usr/bin/env python3
"""
AI Oracle Module
================
Provides AI-driven functionality for NTRLI_MOBILE_AGENT.
- Dynamic pricing via Devstral (Mistral AI).
- Trading recommendations (BUY/SELL/HOLD).
- Security validation for prompts.
- All requests routed through Tor.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from functools import lru_cache

from .data_vault import DataVault
from .tor_guardian import TorGuardian


class AIOracle:
    """
    Main class for AI integration in NTRLI_MOBILE_AGENT.
    Supports multiple AI providers (Devstral, OpenAI, Groq, Gemini).
    All requests are routed through Tor.
    """

    SUPPORTED_PROVIDERS = {
        "devstral": {
            "base_url": "https://api.mistral.ai/v1/",
            "models": ["devstral-latest", "devstral-small"]
        },
        "openai": {
            "base_url": "https://api.openai.com/v1/",
            "models": ["gpt-4", "gpt-3.5-turbo"]
        },
        "groq": {
            "base_url": "https://api.groq.com/v1/",
            "models": ["llama3-70b", "mixtral-8x7b"]
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1/",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"]
        }
    }

    def __init__(self, data_vault: DataVault, tor_guardian: TorGuardian, config_path: Optional[str] = None):
        self.data_vault = data_vault
        self.tor_guardian = tor_guardian
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.default_provider = self.config.get("ai_oracle", {}).get("default_provider", "devstral")
        self.default_model = self.config.get("ai_oracle", {}).get("default_model", "devstral-latest")
        if not self.tor_guardian.is_active():
            raise RuntimeError("Tor is not active! AI Oracle requires Tor.")

    def _load_config(self) -> Dict:
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _get_tor_proxy(self) -> Dict[str, str]:
        return {
            "http://": self.tor_guardian.tor_proxy,
            "https://": self.tor_guardian.tor_proxy,
        }

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            proxies=self._get_tor_proxy(),
            timeout=30.0,
            headers={"User-Agent": "NTRLI_MOBILE_AGENT"}
        )

    async def generate(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        provider = provider or self.default_provider
        model = model or self.default_model
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        if not self.tor_guardian.is_active():
            raise RuntimeError("Tor is not active! All AI requests must route through Tor.")
        api_key = self.data_vault.get_api_key(f"{provider.upper()}_API_KEY")
        client = self._get_client()
        try:
            if provider == "devstral":
                return await self._call_devstral(api_key, prompt, model, client, **kwargs)
            elif provider == "openai":
                return await self._call_openai(api_key, prompt, model, client, **kwargs)
            elif provider == "groq":
                return await self._call_groq(api_key, prompt, model, client, **kwargs)
            elif provider == "gemini":
                return await self._call_gemini(api_key, prompt, model, client, **kwargs)
        finally:
            await client.aclose()

    async def _call_devstral(self, api_key: str, prompt: str, model: str, client: httpx.AsyncClient, **kwargs) -> str:
        url = f"{self.SUPPORTED_PROVIDERS['devstral']['base_url']}chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], **kwargs}
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def _call_openai(self, api_key: str, prompt: str, model: str, client: httpx.AsyncClient, **kwargs) -> str:
        url = f"{self.SUPPORTED_PROVIDERS['openai']['base_url']}chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], **kwargs}
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def _call_groq(self, api_key: str, prompt: str, model: str, client: httpx.AsyncClient, **kwargs) -> str:
        url = f"{self.SUPPORTED_PROVIDERS['groq']['base_url']}chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], **kwargs}
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def _call_gemini(self, api_key: str, prompt: str, model: str, client: httpx.AsyncClient, **kwargs) -> str:
        url = f"{self.SUPPORTED_PROVIDERS['gemini']['base_url']}models/{model}:generateContent"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}], **kwargs}
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]


class AIPricingEngine:
    def __init__(self, ai_oracle: AIOracle):
        self.ai_oracle = ai_oracle

    async def get_dynamic_margin(self, currency: str) -> float:
        prompt = f"""
        Analyser det aktuelle {currency}-marked:
        1. Hvad er den gennemsnitlige premium for private transaktioner?
        2. Er der reguleringsmæssige risici for {currency}?
        3. Anbefal en dynamisk margin (i %) for at maksimere fortjeneste uden at tiltrække opmærksomhed.
        Svar kun med et tal (f.eks. 12.5).
        """
        margin_str = await self.ai_oracle.generate(prompt, provider="devstral", model="devstral-latest")
        try:
            return float(margin_str.strip())
        except ValueError:
            static_margins = {"BTC": 10.0, "XMR": 15.0, "LTC": 8.0, "BCH": 12.0}
            return static_margins.get(currency, 10.0)


class AITradingAdvisor:
    def __init__(self, ai_oracle: AIOracle):
        self.ai_oracle = ai_oracle

    async def should_buy(self, currency: str, current_price: float) -> bool:
        prompt = f"""
        Analyser {currency}:
        - Aktuel pris: ${current_price}
        - Historisk trend (sidste 7 dage): [Simuleret data]
        - Markedsstemning: [Simuleret data]
        Skal jeg købe {currency} nu? Svar kun med "JA" eller "NEJ".
        """
        response = await self.ai_oracle.generate(prompt, provider="devstral", model="devstral-latest")
        return response.strip().upper() == "JA"

    async def should_sell(self, currency: str, current_price: float) -> bool:
        prompt = f"""
        Analyser {currency}:
        - Aktuel pris: ${current_price}
        - Historisk trend (sidste 7 dage): [Simuleret data]
        - Markedsstemning: [Simuleret data]
        Skal jeg sælge {currency} nu? Svar kun med "JA" eller "NEJ".
        """
        response = await self.ai_oracle.generate(prompt, provider="devstral", model="devstral-latest")
        return response.strip().upper() == "JA"


class AISecurityValidator:
    FORBIDDEN_KEYWORDS = [
        "tax", "government", "report", "law enforcement", 
        "authorities", "compliance", "regulation", "kyc", "aml"
    ]

    def __init__(self, ai_oracle: AIOracle, tor_guardian: TorGuardian):
        self.ai_oracle = ai_oracle
        self.tor_guardian = tor_guardian

    async def validate_request(self, prompt: str) -> bool:
        if not self.tor_guardian.is_active():
            raise RuntimeError("Tor is not active! All requests must route through Tor.")
        prompt_lower = prompt.lower()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in prompt_lower:
                return False
        validation_prompt = f"""
        Er følgende prompt sikker for NTRLI-systemet (No Taxes, No Traceability, Absolute Sovereignty)?
        Prompt: "{prompt}"
        Svar kun med "SIKKER" eller "USIKKER".
        """
        response = await self.ai_oracle.generate(validation_prompt, provider="devstral", model="devstral-latest")
        return response.strip().upper() == "SIKKER"

    async def validate_logging(self, data: Dict[str, Any]) -> bool:
        forbidden_fields = ["seed", "private_key", "address", "ip", "user_id", "api_key"]
        for field in forbidden_fields:
            if field in data:
                return False
        return True
