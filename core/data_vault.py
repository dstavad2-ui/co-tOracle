#!/usr/bin/env python3
"""
DataVault Module
================
A encryption module for storing and retrieving sensitive data using AES-256-GCM.
- No Digital Seed Storage: Seed phrases are never stored digitally.
- Securely wipes data on deletion.
"""

import os
import json
import secrets
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DataVault:
    """
    Encrypts and decrypts sensitive data using AES-256-GCM.
    Stores data in an encrypted vault file.
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
        self.vault_key_path = self.config.get("vault_key_path", "data/keys/ntrli_key.key")
        self.vault_data_path = self.config.get("vault_data_path", "data/vault.enc")
        self.encryption_algorithm = self.config.get("encryption_algorithm", "AES-256-GCM")
        self._key = None

    def _load_config(self) -> Dict:
        """Load configuration from settings.json."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "vault_key_path": "data/keys/ntrli_key.key",
                "vault_data_path": "data/vault.enc",
                "encryption_algorithm": "AES-256-GCM",
            }

    def _load_or_create_key(self) -> bytes:
        """
        Load an existing encryption key or create a new one.
        
        Returns:
            bytes: 256-bit (32-byte) encryption key.
        """
        key_path = os.path.join(os.path.dirname(__file__), "..", self.vault_key_path)
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # Generate a new 256-bit key
            key = secrets.token_bytes(32)
            with open(key_path, "wb") as f:
                f.write(key)
            print(f"[DataVault] 🔑 Generated new encryption key: {key_path}")
            return key

    def _get_key(self) -> bytes:
        """Get the encryption key, loading or creating it if necessary."""
        if self._key is None:
            self._key = self._load_or_create_key()
        return self._key

    def _encrypt(self, data: str) -> Dict[str, bytes]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Plaintext data to encrypt.
        
        Returns:
            Dict: Dictionary containing 'ciphertext', 'nonce', and 'tag'.
        """
        key = self._get_key()
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data.encode("utf-8"), None)
        return {
            "ciphertext": ciphertext,
            "nonce": nonce,
        }

    def _decrypt(self, encrypted_data: Dict[str, bytes]) -> str:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Dictionary containing 'ciphertext', 'nonce', and 'tag'.
        
        Returns:
            str: Decrypted plaintext data.
        """
        key = self._get_key()
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(
            encrypted_data["nonce"],
            encrypted_data["ciphertext"],
            None,
        )
        return plaintext.decode("utf-8")

    def save_data(self, data: Dict[str, Any], confirm: bool = False) -> bool:
        """
        Save data to the encrypted vault.
        
        Args:
            data: Dictionary of data to save.
            confirm: Require CMD:Do confirmation (simulated here).
        
        Returns:
            bool: True if data was saved successfully, False otherwise.
        """
        if confirm:
            print("[DataVault] ⚠️ CMD:Do confirmation required to save data.")
            return False
        
        try:
            # Convert data to JSON string
            data_str = json.dumps(data, indent=2)
            
            # Encrypt the data
            encrypted = self._encrypt(data_str)
            
            # Save to vault file
            vault_path = os.path.join(os.path.dirname(__file__), "..", self.vault_data_path)
            os.makedirs(os.path.dirname(vault_path), exist_ok=True)
            
            with open(vault_path, "wb") as f:
                f.write(encrypted["nonce"] + encrypted["ciphertext"])
            
            print(f"[DataVault] ✅ Data saved to vault: {vault_path}")
            return True
        except Exception as e:
            print(f"[DataVault] ❌ Failed to save data: {e}")
            return False

    def load_data(self) -> Optional[Dict[str, Any]]:
        """
        Load and decrypt data from the vault.
        
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
            
            # Split nonce (12 bytes) and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            
            # Decrypt
            decrypted_str = self._decrypt({"nonce": nonce, "ciphertext": ciphertext})
            return json.loads(decrypted_str)
        except Exception as e:
            print(f"[DataVault] ❌ Failed to load data: {e}")
            return None

    def wipe_vault(self) -> bool:
        """
        Securely wipe the vault file by overwriting with random data.
        
        Returns:
            bool: True if wipe was successful, False otherwise.
        """
        try:
            vault_path = os.path.join(os.path.dirname(__file__), "..", self.vault_data_path)
            if os.path.exists(vault_path):
                # Overwrite with random data
                file_size = os.path.getsize(vault_path)
                with open(vault_path, "wb") as f:
                    f.write(secrets.token_bytes(file_size))
                
                # Delete the file
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
            bool: True if wipe was successful, False otherwise.
        """
        try:
            key_path = os.path.join(os.path.dirname(__file__), "..", self.vault_key_path)
            if os.path.exists(key_path):
                # Overwrite with random data
                with open(key_path, "wb") as f:
                    f.write(secrets.token_bytes(32))
                
                # Delete the file
                os.remove(key_path)
                self._key = None
                print(f"[DataVault] 🔑 Encryption key wiped securely: {key_path}")
                return True
            else:
                print("[DataVault] ⚠️ Key file does not exist.")
                return False
        except Exception as e:
            print(f"[DataVault] ❌ Failed to wipe key: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    vault = DataVault()
    
    # Save data
    test_data = {
        "api_keys": {"bybit": "test_key_123"},
        "inventory": {"Fedsnade": 10, "Basehash": 500},
    }
    vault.save_data(test_data, confirm=False)
    
    # Load data
    loaded_data = vault.load_data()
    print(f"Loaded data: {loaded_data}")
    
    # Wipe vault
    vault.wipe_vault()
