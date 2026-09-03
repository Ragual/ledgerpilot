import csv
from collections import Counter


def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


payments = load_csv(
    "data/payments.csv"
)

results = load_csv(
    "data/reconciliation.csv"
)


total_transactions = len(payments)

counts = Counter(
    row["result"]
    for row in results
)


matched = counts.get(
    "MATCHED",
    0
)

failed = counts.get(
    "FAILED_PAYMENT",
    0
)

exceptions = (
    total_transactions
    - matched
    - failed
)


# ==========================================
# Exception counts
# ==========================================

amount_mismatch = counts.get(
    "AMOUNT_MISMATCH",
    0
)

partial_settlement = counts.get(
    "PARTIAL_SETTLEMENT",
    0
)

missing_settlement = counts.get(
    "MISSING_SETTLEMENT",
    0
)

duplicate_settlement = counts.get(
    "DUPLICATE_SETTLEMENT",
    0
)

unexpected_settlement = counts.get(
    "UNEXPECTED_SETTLEMENT",
    0
)


# ==========================================
# Match rate
# ==========================================

match_rate = (
    matched / total_transactions * 100
    if total_transactions > 0
    else 0
)


# ==========================================
# Exception exposure
# ==========================================

exception_value = 0.0

for row in results:

    if row["result"] in [
        "AMOUNT_MISMATCH",
        "PARTIAL_SETTLEMENT",
        "MISSING_SETTLEMENT",
        "DUPLICATE_SETTLEMENT",
        "UNEXPECTED_SETTLEMENT"
    ]:

        exception_value += float(
            row["payment_amount"]
        )


# ==========================================
# Actual discrepancy amount
# ==========================================

discrepancy_value = 0.0

for row in results:

    if row["result"] in [
        "AMOUNT_MISMATCH",
        "PARTIAL_SETTLEMENT"
    ]:

        difference = abs(
            float(row["payment_amount"])
            - float(row["bank_amount"])
        )

        discrepancy_value += difference


# ==========================================
# Output
# ==========================================

print(
    "\n===== LEDGERPILOT EVALUATION ====="
)

print(
    f"\nTotal transactions: "
    f"{total_transactions}"
)

print(
    f"Matched: "
    f"{matched}"
)

print(
    f"Failed payments: "
    f"{failed}"
)

print(
    f"Amount mismatches: "
    f"{amount_mismatch}"
)

print(
    f"Partial settlements: "
    f"{partial_settlement}"
)

print(
    f"Missing settlements: "
    f"{missing_settlement}"
)

print(
    f"Duplicate settlements: "
    f"{duplicate_settlement}"
)

if unexpected_settlement > 0:

    print(
        f"Unexpected settlements: "
        f"{unexpected_settlement}"
    )


print(
    f"\nTotal exceptions: "
    f"{exceptions}"
)

print(
    f"Automatic match rate: "
    f"{match_rate:.2f}%"
)

print(
    f"Exception exposure: "
    f"₹{exception_value:,.2f}"
)

print(
    f"Actual discrepancy amount: "
    f"₹{discrepancy_value:,.2f}"
)


print(
    "\n===== PERFORMANCE SUMMARY ====="
)

print(
    f"✅ Transactions processed: "
    f"{total_transactions}"
)

print(
    f"✅ Automatically matched: "
    f"{matched}"
)

print(
    f"⚠️ Exceptions detected: "
    f"{exceptions}"
)

print(
    f"💰 Exception exposure: "
    f"₹{exception_value:,.2f}"
)

print(
    f"📉 Actual discrepancy: "
    f"₹{discrepancy_value:,.2f}"
)