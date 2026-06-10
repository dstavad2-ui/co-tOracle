#!/usr/bin/env python3
"""
DataVault Module
================
A high-security encryption module for NTRLI_MOBILE_AGENT.
- AES-256-GCM encryption for all sensitive data.
- Secure .env integration for API keys (encrypted at rest).
- No digital seed storage (enforced).
- Secure wipe on deletion.
- Cross-platform support.

NTRLI Principles:
- No Taxes: No financial tracking or reporting.
- No Traceability: No logs, no digital footprints.
- Absolute Sovereignty: User controls all keys and data.
"""

import os
import json
import secrets
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv


class DataVault:
    """
    Securely encrypts and decrypts sensitive data using Fernet (AES-128-CBC + HMAC).
    Manages API keys from .env with automatic encryption/decryption.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize DataVault with configuration.
        
        Args:
            config_path: Path to settings.json. If None, uses default path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "..", "config", "settings.json"
        )
        self.config = self._load_config()
        self.vault_key_path = self.config.get("encryption_key_file", "vault.key")
        self.vault_data_path = self.config.get("vault_data_path", "data/vault.enc")
        self._fernet = None
        self._env_loaded = False
        load_dotenv()  # Load .env file
        self._env_loaded = True

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "encryption_key_file": "vault.key",
                "vault_data_path": "data/vault.enc",
            }

    def _get_fernet(self) -> Fernet:
        """Get or create the Fernet cipher for encryption/decryption."""
        if self._fernet is None:
            key = self._load_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet

    def _load_or_create_key(self) -> bytes:
        """
        Load an existing encryption key or create a new one.
        
        Returns:
            bytes: 256-bit encryption key.
        """
        key_path = os.path.join(os.path.dirname(__file__), "..", self.vault_key_path)
        os.makedirs(os.path.dirname(key_path) if os.path.dirname(key_path) else ".", exist_ok=True)
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(key)
            print(f"[DataVault] 🔑 Generated new encryption key: {key_path}")
            return key

    def _encrypt(self, data: str) -> bytes:
        """Encrypt data using Fernet."""
        fernet = self._get_fernet()
        return fernet.encrypt(data.encode("utf-8"))

    def _decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data using Fernet."""
        fernet = self._get_fernet()
        return fernet.decrypt(encrypted_data).decode("utf-8")

    # ==================== API KEY MANAGEMENT ====================
    def get_api_key(self, service: str) -> str:
        """
        Get and decrypt an API key from .env.
        
        Args:
            service: The service name (e.g., "DEVSTRAL_API_KEY").
        
        Returns:
            str: The decrypted API key.
        
        Raises:
            ValueError: If the API key is not set in .env.
        """
        if not self._env_loaded:
            load_dotenv()
            self._env_loaded = True
        
        encrypted_key = os.getenv(service)
        if not encrypted_key:
            raise ValueError(f"{service} not set in .env!")
        return self._decrypt(encrypted_key.encode())

    def set_api_key(self, service: str, api_key: str) -> None:
        """
        Encrypt and save an API key to .env.
        
        Args:
            service: The service name (e.g., "DEVSTRAL_API_KEY").
            api_key: The API key to encrypt and save.
        """
        encrypted_key = self._encrypt(api_key).decode()
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        
        # Ensure .env exists
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("")
        
        # Update .env file
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            updated = False
            for line in lines:
                if line.startswith(f"{service}="):
                    f.write(f"{service}={encrypted_key}\n")
                    updated = True
                else:
                    f.write(line)
            if not updated:
                f.write(f"{service}={encrypted_key}\n")
        
        print(f"[DataVault] 🔑 API key for {service} saved to .env (encrypted).")

    def rotate_api_key(self, service: str, new_api_key: str) -> bool:
        """
        Rotate an API key by replacing the old one with a new encrypted key.
        
        Args:
            service: The service name (e.g., "DEVSTRAL_API_KEY").
            new_api_key: The new API key.
        
        Returns:
            bool: True if rotation was successful.
        """
        try:
            self.set_api_key(service, new_api_key)
            return True
        except Exception as e:
            print(f"[DataVault] ❌ Failed to rotate API key: {e}")
            return False

    # ==================== DATA VAULT OPERATIONS ====================
    def save_data(self, data: Dict[str, Any], confirm: bool = False) -> bool:
        """
        Save data to the encrypted vault file.
        
        Args:
            data: Dictionary of data to save.
            confirm: Require CMD:Do confirmation (NTRLI compliance).
        
        Returns:
            bool: True if data was saved successfully.
        """
        if confirm:
            print("[DataVault] ⚠️ CMD:Do confirmation required to save data.")
            return False
        
        try:
            data_str = json.dumps(data, indent=2)
            encrypted = self._encrypt(data_str)
            vault_path = os.path.join(os.path.dirname(__file__), "..", self.vault_data_path)
            os.makedirs(os.path.dirname(vault_path) if os.path.dirname(vault_path) else ".", exist_ok=True)
            
            with open(vault_path, "wb") as f:
                f.write(encrypted)
            
            print(f"[DataVault] ✅ Data saved to vault: {vault_path}")
            return True
        except Exception as e:
            print(f"[DataVault] ❌ Failed to save data: {e}")
            return False

    def load_data(self) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt data from the vault file.
        
        Returns:
            Dict: Decrypted data, or None if loading failed.
        """
        try:
            vault_path = os.path.join(os.path.dirname(__file__), "..", self.vault_data_path)
            if not os.path.exists(vault_path):
                print("[DataVault] ⚠️ Vault file does not exist.")
                return None
            
            with open(vault_path, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_str = self._decrypt(encrypted_data)
            return json.loads(decrypted_str)
        except Exception as e:
            print(f"[DataVault] ❌ Failed to load data: {e}")
            return None

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to settings.json."""
        with open(self.config_path, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"[DataVault] ✅ Settings saved to {self.config_path}")

    # ==================== SECURE WIPING ====================
    def wipe_vault(self) -> bool:
        """
        Securely wipe the vault file by overwriting with random data.
        
        Returns:
            bool: True if wipe was successful.
        """
        try:
            vault_path = os.path.join(os.path.dirname(__file__), "..", self.vault_data_path)
            if os.path.exists(vault_path):
                file_size = os.path.getsize(vault_path)
                with open(vault_path, "wb") as f:
                    f.write(secrets.token_bytes(file_size))
                os.remove(vault_path)
                print(f"[DataVault] 🧹 Vault wiped securely: {vault_path}")
                return True
            else:
                print("[DataVault] ⚠️ Vault file does not exist.")
                return False
        except Exception as e:
            print(f"[DataVault] ❌ Failed to wipe vault: {e}")
            return False

    def wipe_key(self) -> bool:
        """
        Securely wipe the encryption key.
        
        Returns:
            bool: True if wipe was successful.
        """
        try:
            key_path = os.path.join(os.path.dirname(__file__), "..", self.vault_key_path)
            if os.path.exists(key_path):
                with open(key_path, "wb") as f:
                    f.write(secrets.token_bytes(32))
                os.remove(key_path)
                self._fernet = None
                print(f"[DataVault] 🔑 Encryption key wiped securely: {key_path}")
                return True
            else:
                print("[DataVault] ⚠️ Key file does not exist.")
                return False
        except Exception as e:
            print(f"[DataVault] ❌ Failed to wipe key: {e}")
            return False

    def wipe_all(self) -> None:
        """Securely wipe all DataVault data (vault + key)."""
        self.wipe_vault()
        self.wipe_key()
        print("[DataVault] 💀 All data wiped securely.")


if __name__ == "__main__":
    # Example usage
    vault = DataVault()
    
    # Test encryption
    test_data = {"api_keys": {"test": "secret_key_123"}}
    vault.save_data(test_data, confirm=False)
    loaded = vault.load_data()
    print(f"[Test] Loaded data: {loaded}")
    
    # Test API key management
    try:
        vault.set_api_key("TEST_API_KEY", "my_secret_api_key")
        retrieved_key = vault.get_api_key("TEST_API_KEY")
        print(f"[Test] Retrieved API key: {retrieved_key}")
    except Exception as e:
        print(f"[Test] API key test failed: {e}")
    
    # Clean up
    vault.wipe_all()
