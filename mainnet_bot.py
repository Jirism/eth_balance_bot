import requests
import time
from datetime import datetime

# TVÉ DATA
API_KEY = "6RR633JY6F6YRQPT4APEVW35DNC1NHHSA5"
ADDRESS = "0x38b9c5A93b48b1E742ee4cDc327C72FAE2519710"
MIN_REWARD = 0.001  # minimum ETH pro „záznam do logu“

def check_rewards():
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
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        print(f"[{datetime.now()}] Chyba při volání API:", e)
        return

    if data["status"] != "1":
        print(f"[{datetime.now()}] Chyba API:", data.get("message"))
        return

    balance_wei = int(data["result"])
    reward_amount = balance_wei / 1e18  # převod z wei na ETH

    print(f"[{datetime.now()}] Stav účtu: {reward_amount} ETH")

    if reward_amount >= MIN_REWARD:
        print("Odměna stojí za to, ukládám do logu")
        with open("log.txt", "a") as f:
            f.write(f"{datetime.now()} - BALANCE {reward_amount} ETH\n")
    else:
        print("Odměna je moc malá, čekám")

# hlavní blok
print("Bot spuštěn")

while True:
    check_rewards()
    time.sleep(10)  # 1 hodina
