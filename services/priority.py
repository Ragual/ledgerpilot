import csv
import json


def load_csv(filename):
    with open(filename, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_json(filename):
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def calculate_priority(transaction, ai_result):
    payment_amount = float(transaction["payment_amount"])
    bank_amount = float(transaction["bank_amount"])

    difference = abs(payment_amount - bank_amount)

    exception_type = transaction["result"]

    risk = ai_result.get("risk", "HIGH")
    confidence = float(
        ai_result.get("confidence", 0)
    )

    # =====================================================
    # 1. Financial exposure score: 0–40
    # =====================================================

    # For missing/partial settlement, use the unsettled
    # amount. For mismatches, use the actual discrepancy.
    if exception_type in [
        "MISSING_SETTLEMENT",
        "PARTIAL_SETTLEMENT"
    ]:
        financial_amount = difference
    else:
        financial_amount = difference

    if financial_amount >= 5000:
        financial_score = 40

    elif financial_amount >= 2500:
        financial_score = 32

    elif financial_amount >= 1000:
        financial_score = 24

    elif financial_amount >= 500:
        financial_score = 18

    elif financial_amount >= 100:
        financial_score = 12

    elif financial_amount > 0:
        financial_score = 6

    else:
        financial_score = 0


    # =====================================================
    # 2. Exception severity score: 0–30
    # =====================================================

    severity_scores = {
        "MISSING_SETTLEMENT": 30,
        "DUPLICATE_SETTLEMENT": 27,
        "PARTIAL_SETTLEMENT": 24,
        "AMOUNT_MISMATCH": 12,
        "UNEXPECTED_SETTLEMENT": 30
    }

    severity_score = severity_scores.get(
        exception_type,
        15
    )


    # =====================================================
    # 3. Risk score: 0–20
    # =====================================================

    risk_scores = {
        "HIGH": 20,
        "MEDIUM": 10,
        "LOW": 3
    }

    risk_score = risk_scores.get(
        risk,
        20
    )


    # =====================================================
    # 4. Uncertainty score: 0–10
    # =====================================================

    if confidence < 0.60:
        uncertainty_score = 10

    elif confidence < 0.70:
        uncertainty_score = 8

    elif confidence < 0.80:
        uncertainty_score = 6

    elif confidence < 0.90:
        uncertainty_score = 3

    else:
        uncertainty_score = 0


    # =====================================================
    # Final weighted score
    # =====================================================

    score = (
        financial_score
        + severity_score
        + risk_score
        + uncertainty_score
    )

    # Safety guarantee: score is always 0–100
    score = max(
        0,
        min(100, score)
    )


    # =====================================================
    # Priority level
    # =====================================================

    if score >= 80:
        priority = "CRITICAL"

    elif score >= 60:
        priority = "HIGH"

    elif score >= 35:
        priority = "MEDIUM"

    else:
        priority = "LOW"


    return (
        score,
        priority,
        difference
    )


# =========================================================
# Load data
# =========================================================

transactions = load_csv(
    "data/diagnosed_transactions.csv"
)

ai_results = load_json(
    "data/real_ai_investigations.json"
)


ai_lookup = {
    item["transaction_id"]: item
    for item in ai_results
}


# =========================================================
# Process exceptions
# =========================================================

exception_types = [
    "MISSING_SETTLEMENT",
    "AMOUNT_MISMATCH",
    "PARTIAL_SETTLEMENT",
    "DUPLICATE_SETTLEMENT",
    "UNEXPECTED_SETTLEMENT"
]


prioritized = []


for transaction in transactions:

    if transaction["result"] not in exception_types:
        continue

    transaction_id = transaction[
        "transaction_id"
    ]

    ai_result = ai_lookup.get(
        transaction_id,
        {
            "risk": "HIGH",
            "confidence": 0
        }
    )

    score, priority, difference = (
        calculate_priority(
            transaction,
            ai_result
        )
    )

    prioritized.append({
        "transaction_id": transaction_id,
        "payment_amount": float(
            transaction["payment_amount"]
        ),
        "bank_amount": float(
            transaction["bank_amount"]
        ),
        "difference": difference,
        "exception_type": transaction["result"],
        "risk": ai_result.get(
            "risk",
            "HIGH"
        ),
        "confidence": float(
            ai_result.get(
                "confidence",
                0
            )
        ),
        "priority_score": score,
        "priority": priority
    })


# Highest priority first
prioritized.sort(
    key=lambda x: (
        x["priority_score"],
        x["difference"]
    ),
    reverse=True
)


# =========================================================
# Save results
# =========================================================

with open(
    "data/priority_results.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        prioritized,
        file,
        indent=4
    )


# =========================================================
# Display top 15
# =========================================================

print(
    "\n===== LEDGERPILOT PRIORITY ENGINE ====="
)

for item in prioritized[:15]:

    print(
        f"\n{item['transaction_id']}"
    )

    print(
        f"Exception: "
        f"{item['exception_type']}"
    )

    print(
        f"Payment: "
        f"₹{item['payment_amount']:,.2f}"
    )

    print(
        f"Difference / Unsettled: "
        f"₹{item['difference']:,.2f}"
    )

    print(
        f"Risk: "
        f"{item['risk']}"
    )

    print(
        f"Confidence: "
        f"{item['confidence'] * 100:.1f}%"
    )

    print(
        f"Priority Score: "
        f"{item['priority_score']}/100"
    )

    print(
        f"Priority: "
        f"{item['priority']}"
    )


# =========================================================
# Summary
# =========================================================

summary = {}

for item in prioritized:

    level = item["priority"]

    summary[level] = (
        summary.get(level, 0) + 1
    )


print(
    "\n===== PRIORITY SUMMARY ====="
)

for level in [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW"
]:

    print(
        f"{level}: "
        f"{summary.get(level, 0)}"
    )


print(
    f"\nTotal exceptions prioritized: "
    f"{len(prioritized)}"
)

print(
    "\n✅ Priority analysis completed!"
)

print(
    "📁 Saved to: data/priority_results.json"
)