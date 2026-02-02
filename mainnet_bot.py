import requests
import os
from datetime import datetime

# DATA
API_KEY = os.getenv("ETHERSCAN_API_KEY")  # z GitHub secretu
ADDRESS = "0x38b9c5A93b48b1E742ee4cDc327C72FAE2519710"
MIN_REWARD = 0.001  # minimum ETH pro záznam

def check_rewards():
    if not API_KEY:
        print("Chybí ETHERSCAN_API_KEY")
        return

    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": 1,
        "module": "account",
        "action": "balance",
        "address": ADDRESS,
        "tag": "latest",
        "apikey": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"[{datetime.now()}] Chyba při volání API:", e)
        return

    if data.get("status") != "1":
        print(f"[{datetime.now()}] Chyba API:", data)
        return

    balance_wei = int(data["result"])
    balance_eth = balance_wei / 1e18

    print(f"[{datetime.now()}] Stav účtu: {balance_eth} ETH")

    if balance_eth >= MIN_REWARD:
        with open("log.txt", "a") as f:
            f.write(f"{datetime.now()} - BALANCE {balance_eth} ETH\n")
        print("Uloženo do logu")
    else:
        print("Odměna zatím malá")

def main():
    print("Bot spuštěn")
    check_rewards()
    print("Bot skončil")

if __name__ == "__main__":
    main()

