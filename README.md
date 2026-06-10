# NTRLI_MOBILE_AGENT

**Underground Economic Engine**
*Bureaucratic | Calculative | Accounting*

---

## 📚 Overview

**NTRLI_MOBILE_AGENT** is a fully automated, JSON Schema-compatible agent operating under **NTRLI SLAVE principles** (No Taxes, No Traceability, Absolute Sovereignty). It is designed to handle underground economic operations such as:

- **Salgslogning** (Sales Logging)
- **Marginvalidering** (Margin Validation)
- **Efterspørgselsforudsigelse** (Demand Prediction)
- **Omkostningsberegninger** (Cost Calculations)

The system integrates **Tor**, **Bitcoin Wallets**, and **Bybit API** for **100% anonymity** and **security**.

---

## 🏗️ Architecture

| **Component**       | **Type**               | **Purpose**                                                                                     | **Security Level** | **Anonymity Level** |
|--------------------|------------------------|-----------------------------------------------------------------------------------------------|--------------------|---------------------|
| **NTRLI_MOBILE_AGENT** | **Main Agent**         | Underground Economic Engine. Controls all operations.                                         | ✅✅✅ (Max)        | ✅✅✅ (Max)        |
| **CostOracle**      | **Module**            | Calculates costs, margins, and prices based on static and dynamic data.                      | ✅✅✅             | ✅✅                |
| **TorGuardian**     | **Security Module**   | Ensures **ALL** traffic goes through Tor. Blocks clearnet if Tor fails.                       | ✅✅✅             | ✅✅✅             |
| **DataVault**       | **Encryption Module** | Stores and retrieves data with **AES-256-GCM** encryption.                                   | ✅✅✅             | ✅✅✅             |
| **WalletManager**   | **Wallet Control**    | Manages **Sparrow**, **Wasabi**, and **Electrum** wallets with Tor integration.               | ✅✅✅             | ✅✅✅             |
| **BybitBridge**     | **API Module**        | Handles **Bybit API** requests (deposit, transactions) via Tor.                              | ✅✅✅             | ✅✅✅             |
| **NTRLICore**       | **Kernel**            | Core logic: `log_sale`, `validate_margin`, `predict_demand`, `calculate_extract_cost`.         | ✅✅✅             | ✅✅✅             |

---

## 📁 File Structure

```
ntRLI_mobile_agent/
├── core/
│   ├── __init__.py
│   ├── tor_guardian.py       # TorGuardian module
│   ├── data_vault.py         # DataVault module
│   ├── cost_oracle.py        # CostOracle module
│   ├── wallet_manager.py     # WalletManager module
│   ├── bybit_bridge.py       # BybitBridge module
│   └── ntrli_core.py         # NTRLICore (main kernel)
├── config/
│   ├── settings.json         # Configuration
│   └── schema.json           # JSON Schema for validation
├── data/
│   ├── keys/                 # Encryption keys
│   └── vault.enc             # Encrypted data
├── scripts/
│   ├── ntRLI_master_setup.py # Master setup script
│   └── cli.py                # CLI interface
├── wallets/                  # Wallet files (Sparrow, Wasabi, Electrum)
└── README.md                 # Documentation
```

---

## 🚀 Quick Start

### 1. **Clone the Repository**

```bash
git clone https://github.com/dstavad2-ui/co-tOracle.git
cd co-tOracle
```

### 2. **Install Dependencies**

```bash
pip install requests cryptography psutil
```

### 3. **Install Tor**

- **Linux:**
  ```bash
  sudo apt update && sudo apt install tor
  sudo systemctl start tor
  ```

- **Termux:**
  ```bash
  pkg install tor
  tor
  ```

### 4. **Run the Master Setup Script**

```bash
python3 scripts/ntRLI_master_setup.py --install-deps --test
```

### 5. **Start the CLI**

```bash
python3 scripts/cli.py --interactive
```

---

## 💻 Usage

### **CLI Commands**

| **Command**         | **Description**                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------|
| `CMD:PROTECTOR`    | Activates **TorGuardian** to ensure all traffic is routed through Tor.                             |
| `CMD:Do`           | Confirms actions (e.g., saving data to DataVault).                                                |
| `CMD:SETUP`        | Initializes the system (creates directories, loads modules).                                      |
| `CMD:START`        | Starts all wallets and monitoring.                                                                |
| `CMD:STOP`         | Stops all wallets and monitoring.                                                                 |
| `CMD:TEST`         | Tests all modules (Tor, DataVault, CostOracle, etc.).                                              |
| `CMD:WIPE`         | Securely wipes all system data.                                                                   |
| `CMD:MONITOR`      | Toggles system monitoring (Tor, wallets, transactions).                                          |
| `CMD:SALE`         | Logs a sale (example: `CMD:SALE`).                                                                 |
| `CMD:MARGIN`       | Validates a margin (example: `CMD:MARGIN`).                                                        |
| `CMD:DEMAND`       | Predicts demand (example: `CMD:DEMAND`).                                                           |

### **Example Workflow**

1. **Activate TorGuardian:**
   ```bash
   python3 scripts/cli.py "CMD:PROTECTOR"
   ```

2. **Test the System:**
   ```bash
   python3 scripts/cli.py "CMD:TEST"
   ```

3. **Log a Sale:**
   ```bash
   python3 scripts/cli.py "CMD:SALE"
   ```

4. **Validate a Margin:**
   ```bash
   python3 scripts/cli.py "CMD:MARGIN"
   ```

5. **Predict Demand:**
   ```bash
   python3 scripts/cli.py "CMD:DEMAND"
   ```

---

## 🔐 Security Features

### **TorGuardian**
- **Blocks Clearnet:** If Tor fails, all traffic is blocked using `iptables`.
- **Tor Jail:** Kills critical processes (Sparrow, Wasabi, Electrum) if Tor fails.
- **Continuous Monitoring:** Checks Tor connectivity every 60 seconds.

### **DataVault**
- **AES-256-GCM Encryption:** All sensitive data is encrypted.
- **No Digital Seed Storage:** Seed phrases are **never** stored digitally.
- **Secure Wiping:** Overwrites data with random bytes before deletion.

### **WalletManager**
- **Tor Integration:** All wallet traffic goes through Tor.
- **CoinJoin Support:** Supports **Whirlpool (Sparrow)**, **Chaumian CoinJoin (Wasabi)**, and **Electrum plugins**.
- **New Address per Transaction:** Avoids linking transactions.

### **BybitBridge**
- **HMAC-SHA256 Signing:** Secures API requests.
- **Rate Limiting:** Enforces 20 requests/minute.
- **Tor Proxy:** All API calls go through Tor.

---

## 📊 CostOracle Functions

| **Function**            | **Description**                                                                                     | **Example**                                  |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------|
| `calculate_extract_cost` | Calculates cost per gram of extract based on basehash input.                                      | `calculate_extract_cost(5)` → **70.75 DKK/g** |
| `validate_margin`        | Validates if a price meets NTRLI's margin requirements.                                           | `validate_margin("Fedsnade", 350, "knd")`     |
| `log_sale`               | Logs a sale and updates inventory.                                                                 | `log_sale("Fedsnade", 1, "knd", 350, "XMR")` |
| `predict_demand`         | Predicts demand based on historical sales data.                                                   | `predict_demand("Fedsnade", 7)`               |

### **Margin Requirements**

| **Category** | **Required Margin** |
|-------------|---------------------|
| `knd`       | 85.88%              |
| `ret`       | 70%                 |
| `whs`       | 60%                 |

---

## 🔧 Configuration

### **settings.json**

```json
{
  "tor_proxy": "socks5://127.0.0.1:9050",
  "tor_check_url": "https://check.torproject.org/api/ip",
  "vault_key_path": "data/keys/ntrli_key.key",
  "vault_data_path": "data/vault.enc",
  "critical_processes": ["sparrow", "wasabi", "electrum", "python", "java", "dotnet"],
  "wallet_settings": {
    "sparrow": {
      "path": "wallets/sparrow.jar",
      "proxy_args": "--proxy socks5:127.0.0.1:9050",
      "coinjoin_backend": "whirlpool"
    },
    "wasabi": {
      "path": "wallets/Wasabi.Wallet.Wpf.dll",
      "headless_args": "--headless --proxy socks5://127.0.0.1:9050",
      "coinjoin_enabled": true
    },
    "electrum": {
      "path": "electrum",
      "proxy_args": "--proxy socks5:127.0.0.1:9050",
      "coinjoin_plugin": true
    }
  },
  "bybit_api": {
    "base_url": "https://api.bybit.com",
    "rate_limit": 20,
    "timeout": 10
  },
  "security": {
    "memory_wipe_on_exit": true,
    "max_retries": 3,
    "encryption_algorithm": "AES-256-GCM"
  }
}
```

---

## 🌍 Supported Platforms

| **Platform**       | **Support** | **Notes**                                                                                     |
|--------------------|-------------|-----------------------------------------------------------------------------------------------|
| **Linux**          | ✅ Full     | Requires `tor`, `iptables`, and Python 3.8+.                                                   |
| **Termux (Android)** | ✅ Full   | Requires `tor` and `proot` for `iptables`.                                                     |
| **Windows**        | ⚠️ Partial  | Tor and wallet support may require additional configuration.                                  |
| **MacOS**          | ✅ Full     | Requires `tor` and `iptables` (via Homebrew or manual installation).                          |

---

## 📜 License

This project operates under **NTRLI SLAVE principles**:
- **No Taxes**
- **No Traceability**
- **Absolute Sovereignty**

---

## 🔗 Links

- **GitHub:** [dstavad2-ui/co-tOracle](https://github.com/dstavad2-ui/co-tOracle)
- **Tor Project:** [https://www.torproject.org/](https://www.torproject.org/)
- **Sparrow Wallet:** [https://sparrowwallet.com/](https://sparrowwallet.com/)
- **Wasabi Wallet:** [https://wasabiwallet.io/](https://wasabiwallet.io/)
- **Electrum:** [https://electrum.org/](https://electrum.org/)
- **Bybit API:** [https://bybit-exchange.github.io/docs/](https://bybit-exchange.github.io/docs/)

---

## 🛡️ Disclaimer

This software is for **educational purposes only**. The authors are not responsible for any misuse or illegal activities. Always comply with local laws and regulations.
