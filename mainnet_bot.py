import os
from datetime import datetime
import logging
import json
from web3 import Web3
from decimal import Decimal

# ---------- Cesty ----------
BASE_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(BASE_DIR, "log.txt")
LAST_BALANCE_FILE = os.path.join(BASE_DIR, "last_balance.json")
LOCK_FILE = os.path.join(BASE_DIR, "bot.lock")

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ---------- LOCK ----------
def acquire_lock():
    if os.path.exists(LOCK_FILE):
        logging.warning("Bot už běží – ukončuji.")
        raise SystemExit("LOCK aktivní.")
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# ---------- Konfigurace ----------
INFURA_URL = os.getenv("RPC_URL")  # ← bude z GitHub Secret
ADDRESS = Web3.to_checksum_address("0x38b9c5A93b48b1E742ee4cDc327C72FAE2519710")

MIN_REWARD = Decimal("0.001")
GAS_THRESHOLD = Decimal("30")  # gwei

# 🔐 Bezpečnostní limity (NEPŘEDĚLÁVÁM)
MAX_TX_AMOUNT = Decimal("0.01")
MIN_BALANCE_RESERVE = Decimal("0.002")

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "false"
EXPECTED_CHAIN_ID = 1  # Linea Sepolia
TX_ALREADY_SENT = False

# ---------- Web3 ----------
if not INFURA_URL:
    raise SystemExit("RPC_URL není nastaven.")

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

if not w3.is_connected():
    logging.critical("Nepodařilo se připojit k síti ❌")
    raise SystemExit("Síť není dostupná.")
else:
    logging.info("Připojeno k síti ✅")

# ---------- JSON ----------
def load_last_balance():
    if os.path.exists(LAST_BALANCE_FILE):
        with open(LAST_BALANCE_FILE, "r") as f:
            data = json.load(f)
            return Decimal(str(data.get("balance_eth", "0")))
    return Decimal("0")

def save_last_balance(balance_eth):
    with open(LAST_BALANCE_FILE, "w") as f:
        json.dump({"balance_eth": str(balance_eth)}, f)

# ---------- Reward Check ----------
def check_rewards():
    try:
        balance_wei = w3.eth.get_balance(ADDRESS)
        balance_eth = Decimal(balance_wei) / Decimal(10**18)
    except Exception as e:
        logging.error(f"Chyba při čtení balance: {e}")
        return None

    last_balance = load_last_balance()
    reward_diff = balance_eth - last_balance

    latest_block = w3.eth.get_block("latest")
    base_fee = Decimal(latest_block.get("baseFeePerGas", 0))
    priority_fee = Decimal(w3.to_wei(2, "gwei"))
    estimated_gas_cost = ((base_fee + priority_fee) * Decimal(21000)) / Decimal(10**18)

    base_fee_gwei = Decimal(w3.from_wei(base_fee, "gwei"))

    condition_1 = reward_diff >= Decimal("1.5") * estimated_gas_cost
    condition_2 = (reward_diff - estimated_gas_cost) >= Decimal("0.0002")
    condition_3 = base_fee_gwei <= GAS_THRESHOLD
    condition_4 = reward_diff >= MIN_REWARD

    should_collect = all([condition_1, condition_2, condition_3, condition_4])

    logging.info(f"Balance: {balance_eth:.6f} ETH")
    logging.info(f"Reward diff: {reward_diff:.6f} ETH")
    logging.info(f"Odhad gas cost: {estimated_gas_cost:.6f} ETH")
    logging.info(f"Base fee: {base_fee_gwei} gwei")
    logging.info(f"Collect? {'ANO' if should_collect else 'NE'}")

    save_last_balance(balance_eth)

    return should_collect

# ---------- SEND ETH ----------
def send_eth(to_address, amount_eth):
    global TX_ALREADY_SENT

    if TX_ALREADY_SENT:
        logging.warning("Transakce už byla v tomto běhu odeslána.")
        return

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        logging.error("PRIVATE_KEY není nastaven.")
        return

    to_address = Web3.to_checksum_address(to_address)

    if w3.eth.chain_id != EXPECTED_CHAIN_ID:
        logging.error(f"ŠPATNÁ SÍŤ! chainId: {w3.eth.chain_id}")
        return

    account = w3.eth.account.from_key(private_key)
    if account.address.lower() != ADDRESS.lower():
        logging.error("PRIVATE KEY neodpovídá ADDRESS!")
        return

    if amount_eth > MAX_TX_AMOUNT:
        logging.error("Překročen MAX_TX_AMOUNT!")
        return

    try:
        balance_eth = Decimal(w3.eth.get_balance(ADDRESS)) / Decimal(10**18)

        if amount_eth > (balance_eth - MIN_BALANCE_RESERVE):
            logging.error("Nedostatek prostředků po rezervě.")
            return

        nonce = w3.eth.get_transaction_count(ADDRESS, "pending")

        latest_block = w3.eth.get_block("latest")
        base_fee = Decimal(latest_block.get("baseFeePerGas", 0))
        priority_fee = Decimal(w3.to_wei(2, "gwei"))
        max_fee = base_fee + priority_fee

        base_fee_gwei = Decimal(w3.from_wei(base_fee, "gwei"))

        if base_fee_gwei > GAS_THRESHOLD:
            logging.warning(f"Gas moc vysoký ({base_fee_gwei} gwei) – neposílám.")
            return

        tx = {
            "nonce": nonce,
            "to": to_address,
            "value": w3.to_wei(amount_eth, "ether"),
            "gas": 21000,
            "maxFeePerGas": int(max_fee),
            "maxPriorityFeePerGas": int(priority_fee),
            "chainId": EXPECTED_CHAIN_ID,
            "type": 2
        }

        if DRY_RUN:
            logging.info("🧪 DRY RUN – transakce NEBUDE odeslána.")
            logging.info(f"Simulace TX: {tx}")
            return "DRY_RUN"

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        TX_ALREADY_SENT = True
        logging.info(f"TX odeslána: {tx_hash.hex()}")
        return tx_hash.hex()

    except Exception as e:
        logging.error(f"Chyba při odesílání: {e}")

# ---------- MAIN ----------
def main():
    acquire_lock()
    try:
        logging.info("Bot spuštěn")

        if check_rewards():
            logging.info("Podmínky splněny → odesílám 0.0001 ETH")
            send_eth(ADDRESS, Decimal("0.0001"))

        logging.info("Bot skončil")
    finally:
        release_lock()

if __name__ == "__main__":
    main()














