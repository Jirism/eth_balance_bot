import requests
from datetime import datetime

API_KEY = "6RR633JY6F6YRQPT4APEVW35DNC1NHHSA5"
ADDRESS = "0x38b9c5A93b48b1E742ee4cDc327C72FAE2519710"

url = (
    "https://api.etherscan.io/v2/api"
    f"?chainid=1"
    f"&module=account"
    f"&action=balance"
    f"&address={ADDRESS}"
    f"&tag=latest"
    f"&apikey={API_KEY}"
)

response = requests.get(url)
data = response.json()

print(data)

if data["status"] == "1":
    balance_wei = int(data["result"])
    balance_eth = balance_wei / 1e18
    print(f"Zůstatek: {balance_eth} ETH")
else:
    print("Chyba:", data["result"])

