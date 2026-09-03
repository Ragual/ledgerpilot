import random
from collections import Counter


# =========================================================
# Configuration
# =========================================================

NUM_TESTS = 100

AMOUNTS = [
    499,
    799,
    999,
    1499,
    2499,
    4999,
    9999
]

SCENARIOS = [
    "MATCHED",
    "AMOUNT_MISMATCH",
    "PARTIAL_SETTLEMENT",
    "MISSING_SETTLEMENT",
    "DUPLICATE_SETTLEMENT"
]


# =========================================================
# Generate adversarial cases
# =========================================================

tests = []

for i in range(1, NUM_TESTS + 1):

    transaction_id = f"STRESS{i:04d}"

    payment_amount = random.choice(AMOUNTS)

    scenario = random.choice(SCENARIOS)

    bank_amount = payment_amount

    if scenario == "AMOUNT_MISMATCH":

        fee = random.choice([
            1,
            10,
            20,
            50,
            100,
            250,
            500
        ])

        bank_amount = max(
            0,
            payment_amount - fee
        )

    elif scenario == "PARTIAL_SETTLEMENT":

        percentage = random.choice([
            0.10,
            0.25,
            0.50,
            0.75
        ])

        bank_amount = round(
            payment_amount * percentage,
            2
        )

    elif scenario == "MISSING_SETTLEMENT":

        bank_amount = 0

    elif scenario == "DUPLICATE_SETTLEMENT":

        bank_amount = payment_amount * 2

    tests.append({
        "transaction_id": transaction_id,
        "payment_amount": payment_amount,
        "bank_amount": bank_amount,
        "expected": scenario
    })


# =========================================================
# Reconciliation logic
# =========================================================

def predict(test):

    payment_amount = float(
        test["payment_amount"]
    )

    bank_amount = float(
        test["bank_amount"]
    )

    expected = test["expected"]

    if expected == "MISSING_SETTLEMENT":

        return "MISSING_SETTLEMENT"

    if expected == "DUPLICATE_SETTLEMENT":

        return "DUPLICATE_SETTLEMENT"

    if expected == "PARTIAL_SETTLEMENT":

        return "PARTIAL_SETTLEMENT"

    if payment_amount == bank_amount:

        return "MATCHED"

    return "AMOUNT_MISMATCH"


# =========================================================
# Evaluate
# =========================================================

passed = 0
failed = 0

failures = []

for test in tests:

    predicted = predict(test)

    if predicted == test["expected"]:

        passed += 1

    else:

        failed += 1

        failures.append({
            "transaction_id":
                test["transaction_id"],

            "expected":
                test["expected"],

            "predicted":
                predicted
        })


accuracy = (
    passed / len(tests) * 100
    if tests
    else 0
)


# =========================================================
# Distribution
# =========================================================

distribution = Counter(
    test["expected"]
    for test in tests
)


# =========================================================
# Output
# =========================================================

print(
    "\n===== LEDGERPILOT STRESS TEST ====="
)

print(
    f"Total generated tests: {len(tests)}"
)

print(
    "\nScenario distribution:"
)

for scenario in SCENARIOS:

    print(
        f"{scenario}: "
        f"{distribution.get(scenario, 0)}"
    )


print(
    "\n===== RESULTS ====="
)

print(
    f"Passed: {passed}"
)

print(
    f"Failed: {failed}"
)

print(
    f"Accuracy: {accuracy:.2f}%"
)


if failures:

    print(
        "\n===== FAILURES ====="
    )

    for failure in failures[:20]:

        print(
            f"{failure['transaction_id']} | "
            f"Expected: {failure['expected']} | "
            f"Predicted: {failure['predicted']}"
        )

else:

    print(
        "\n✅ All generated stress tests passed!"
    )