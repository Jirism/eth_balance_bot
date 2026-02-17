GAS_THRESHOLD = 20  # musí odpovídat hlavnímu scriptu

def simulate(balance_eth, last_balance, gas):
    reward_diff = balance_eth - last_balance
    should_collect = reward_diff > 0 and gas < GAS_THRESHOLD

    print("---------------")
    print(f"Balance: {balance_eth}")
    print(f"Last balance: {last_balance}")
    print(f"Reward diff: {reward_diff}")
    print(f"Gas: {gas}")
    print(f"Should collect? {'ANO' if should_collect else 'NE'}")
    print("---------------\n")


if __name__ == "__main__":
    print("=== TEST LOGIKY ===\n")

    # 🟢 Ideální scénář
    simulate(0.020, 0.010, 15)   # očekáváme ANO

    # 🔴 Gas moc vysoký
    simulate(0.020, 0.010, 40)   # očekáváme NE

    # 🔴 Žádný růst balance
    simulate(0.010, 0.010, 10)   # očekáváme NE

    # 🔴 Balance klesla
    simulate(0.008, 0.010, 10)   # očekáváme NE

    # 🟡 Malý růst + nízký gas
    simulate(0.011, 0.010, 5)    # očekáváme ANO
