#!/usr/bin/env python3
"""
NTRLI_MOBILE_AGENT: Master Setup Script
=====================================
This script sets up the entire NTRLI_MOBILE_AGENT system automatically.
Supports:
- Mistral Studio (temporary directory: /tmp/ntRLI_mobile_agent/)
- Termux/PC (permanent installation)

Usage:
    python3 ntRLI_master_setup.py [--install-deps] [--start-wallets] [--test]

Examples:
    python3 ntRLI_master_setup.py              # Setup files
    python3 ntRLI_master_setup.py --install-deps # Setup + install dependencies
    python3 ntRLI_master_setup.py --start-wallets # Setup + start wallets
    python3 ntRLI_master_setup.py --test        # Setup + test system
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else "/tmp/ntRLI_mobile_agent"
REPO_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
CONFIG_DIR = os.path.join(REPO_ROOT, "config")
CORE_DIR = os.path.join(REPO_ROOT, "core")
DATA_DIR = os.path.join(REPO_ROOT, "data", "keys")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
WALLETS_DIR = os.path.join(REPO_ROOT, "wallets")

# --- Create directories ---
def create_directories():
    """Create all necessary directories."""
    directories = [
        REPO_ROOT,
        CONFIG_DIR,
        CORE_DIR,
        DATA_DIR,
        os.path.join(REPO_ROOT, "data"),
        SCRIPTS_DIR,
        WALLETS_DIR,
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)
    print("[NTRLI] ✅ Directory structure created.")

# --- Install dependencies ---
def install_dependencies():
    """Install Python dependencies using pip."""
    dependencies = [
        "requests",
        "cryptography",
        "psutil",
    ]
    
    print("[NTRLI] 📦 Installing dependencies...")
    for dep in dependencies:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
            )
            print(f"[NTRLI] ✅ Installed: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"[NTRLI] ❌ Failed to install {dep}: {e.stderr.decode()}")
            return False
    return True

# --- Verify Tor ---
def verify_tor():
    """Verify Tor is installed and running."""
    print("[NTRLI] 🔍 Verifying Tor...")
    
    # Check if Tor is installed
    try:
        subprocess.run(["tor", "--version"], check=True, capture_output=True)
        print("[NTRLI] ✅ Tor is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[NTRLI] ⚠️ Tor is not installed. Install Tor first:")
        print("  - Linux: sudo apt install tor")
        print("  - Termux: pkg install tor")
        return False
    
    # Check if Tor is running
    try:
        result = subprocess.run(
            ["pgrep", "-f", "tor"],
            check=True,
            capture_output=True,
        )
        if result.returncode == 0:
            print("[NTRLI] ✅ Tor is running.")
            return True
        else:
            print("[NTRLI] ⚠️ Tor is not running. Start Tor first:")
            print("  - Linux: sudo systemctl start tor")
            print("  - Termux: tor")
            return False
    except Exception as e:
        print(f"[NTRLI] ❌ Error checking Tor: {e}")
        return False

# --- Download wallet files (placeholder) ---
def download_wallets():
    """Download wallet files (Sparrow, Wasabi, Electrum)."""
    print("[NTRLI] 💼 Downloading wallet files...")
    
    # Placeholder: In a real implementation, this would download the wallet files
    wallet_files = {
        "sparrow": "https://sparrowwallet.com/download/sparrow.jar",
        "wasabi": "https://github.com/zkSNACKs/WalletWasabi/releases/download/v2.0.4/Wasabi.Wallet.Wpf.dll",
        "electrum": "https://electrum.org/download/Electrum-4.4.5.tar.gz",
    }
    
    for name, url in wallet_files.items():
        print(f"[NTRLI] ⚠️ Download {name} from {url} (manual download recommended)")
    
    return True

# --- Test system ---
def test_system():
    """Test the entire system."""
    print("[NTRLI] 🧪 Testing system...")
    
    # Add REPO_ROOT to Python path
    sys.path.insert(0, REPO_ROOT)
    
    try:
        from core.ntrli_core import NTRLICore
        core = NTRLICore()
        
        # Test TorGuardian
        if core.tor_guardian.check_tor():
            print("[NTRLI] ✅ TorGuardian: Tor is active")
        else:
            print("[NTRLI] ❌ TorGuardian: Tor is not active")
        
        # Test DataVault
        test_data = {"test": "data"}
        if core.data_vault.save_data(test_data, confirm=False):
            loaded_data = core.data_vault.load_data()
            if loaded_data == test_data:
                print("[NTRLI] ✅ DataVault: Read/write test passed")
                core.data_vault.wipe_vault()
            else:
                print("[NTRLI] ❌ DataVault: Read/write test failed")
        else:
            print("[NTRLI] ❌ DataVault: Failed to save test data")
        
        # Test CostOracle
        extract_cost = core.cost_oracle.calculate_extract_cost(5.0)
        print(f"[NTRLI] ✅ CostOracle: Extract cost for 5g basehash = {extract_cost} DKK/g")
        
        # Test WalletManager
        wallets = core.wallet_manager.list_wallets()
        print(f"[NTRLI] ✅ WalletManager: Configured wallets = {[w['name'] for w in wallets]}")
        
        # Test BybitBridge
        if core.bybit_bridge.test_connectivity():
            print("[NTRLI] ✅ BybitBridge: API connectivity test passed")
        else:
            print("[NTRLI] ❌ BybitBridge: API connectivity test failed")
        
        return True
    except Exception as e:
        print(f"[NTRLI] ❌ System test failed: {e}")
        return False

# --- Main function ---
def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="NTRLI_MOBILE_AGENT Master Setup")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install Python dependencies",
    )
    parser.add_argument(
        "--start-wallets",
        action="store_true",
        help="Start wallets after setup",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test the system after setup",
    )
    parser.add_argument(
        "--download-wallets",
        action="store_true",
        help="Download wallet files",
    )
    
    args = parser.parse_args()
    
    print("""
=====================================
NTRLI_MOBILE_AGENT: Master Setup
=====================================
""")
    
    # Step 1: Create directories
    create_directories()
    
    # Step 2: Install dependencies (if requested)
    if args.install_deps:
        if not install_dependencies():
            print("[NTRLI] ❌ Dependency installation failed. Exiting.")
            sys.exit(1)
    
    # Step 3: Verify Tor
    if not verify_tor():
        print("[NTRLI] ⚠️ Tor is not installed or running. Some features may not work.")
    
    # Step 4: Download wallet files (if requested)
    if args.download_wallets:
        download_wallets()
    
    # Step 5: Test system (if requested)
    if args.test:
        if not test_system():
            print("[NTRLI] ❌ System test failed. Exiting.")
            sys.exit(1)
    
    # Step 6: Start wallets (if requested)
    if args.start_wallets:
        print("[NTRLI] ▶️ Starting wallets...")
        sys.path.insert(0, REPO_ROOT)
        from core.ntrli_core import NTRLICore
        core = NTRLICore()
        core.start_wallets()
    
    print("""
=====================================
NTRLI_MOBILE_AGENT: Setup Complete
=====================================
Next steps:
1. Ensure Tor is running: sudo systemctl start tor
2. Start the CLI: python3 scripts/cli.py --interactive
3. Execute commands: CMD:PROTECTOR, CMD:TEST, etc.
=====================================
""")


if __name__ == "__main__":
    main()
