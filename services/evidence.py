import csv
import json


def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


transactions = load_csv(
    "data/diagnosed_transactions.csv"
)

evidence_results = []


for transaction in transactions:

    result = transaction["result"]

    if result in ["MATCHED", "FAILED_PAYMENT"]:
        continue

    payment_amount = float(
        transaction["payment_amount"]
    )

    bank_amount = float(
        transaction["bank_amount"]
    )

    difference = round(
        payment_amount - bank_amount,
        2
    )

    evidence = []


    # ==========================================
    # Common evidence
    # ==========================================

    evidence.append(
        "Payment transaction exists"
    )

    if result != "FAILED_PAYMENT":

        evidence.append(
            "Payment status is SUCCESS"
        )


    # ==========================================
    # Missing settlement
    # ==========================================

    if result == "MISSING_SETTLEMENT":

        evidence.append(
            "No matching bank settlement was found"
        )

        diagnosis = (
            "Successful payment has no matching "
            "bank settlement"
        )

        confidence = 0.95

        action = (
            "Investigate settlement status "
            "and payout records"
        )

        risk = "HIGH"


    # ==========================================
    # Amount mismatch
    # ==========================================

    elif result == "AMOUNT_MISMATCH":

        evidence.append(
            "Matching transaction ID was found "
            "in bank statement"
        )

        evidence.append(
            f"Bank amount differs from payment by "
            f"₹{abs(difference):.2f}"
        )

        if abs(difference) <= 100:

            evidence.append(
                "Difference is within the configured "
                "fee-adjustment threshold"
            )

            diagnosis = (
                "Likely processing fee or "
                "settlement adjustment"
            )

            confidence = 0.90

            action = (
                "Verify applicable fee "
                "and reconcile"
            )

            risk = "LOW"

        else:

            evidence.append(
                "Difference exceeds the configured "
                "fee-adjustment threshold"
            )

            diagnosis = (
                "Unusual settlement amount difference"
            )

            confidence = 0.75

            action = (
                "Escalate to finance team "
                "for investigation"
            )

            risk = "HIGH"


    # ==========================================
    # Partial settlement
    # ==========================================

    elif result == "PARTIAL_SETTLEMENT":

        evidence.append(
            "Matching transaction ID was found "
            "in bank statement"
        )

        settled_percentage = (
            bank_amount / payment_amount * 100
            if payment_amount > 0
            else 0
        )

        evidence.append(
            f"Only {settled_percentage:.1f}% "
            "of the payment amount was credited"
        )

        evidence.append(
            f"Unsettled amount is "
            f"₹{difference:.2f}"
        )

        diagnosis = (
            "Partial settlement detected"
        )

        confidence = 0.97

        action = (
            "Verify settlement schedule and "
            "remaining payout"
        )

        risk = "HIGH"


    # ==========================================
    # Duplicate settlement
    # ==========================================

    elif result == "DUPLICATE_SETTLEMENT":

        evidence.append(
            "Multiple bank records were found "
            "for the same transaction ID"
        )

        evidence.append(
            f"Combined bank credit is "
            f"₹{bank_amount:.2f}"
        )

        diagnosis = (
            "Duplicate settlement records detected"
        )

        confidence = 0.98

        action = (
            "Investigate duplicate settlement "
            "before reconciliation"
        )

        risk = "HIGH"


    # ==========================================
    # Unknown exception
    # ==========================================

    else:

        evidence.append(
            "Unrecognized reconciliation result"
        )

        diagnosis = (
            "Unknown reconciliation exception"
        )

        confidence = 0.50

        action = (
            "Manual investigation required"
        )

        risk = "HIGH"


    evidence_results.append({
        "transaction_id":
            transaction["transaction_id"],

        "payment_amount":
            payment_amount,

        "bank_amount":
            bank_amount,

        "difference":
            difference,

        "result":
            result,

        "diagnosis":
            diagnosis,

        "confidence":
            confidence,

        "recommended_action":
            action,

        "risk":
            risk,

        "evidence":
            evidence
    })


# ==========================================
# Save evidence results
# ==========================================

with open(
    "data/evidence_results.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        evidence_results,
        file,
        indent=4
    )


# ==========================================
# Summary
# ==========================================

counts = {}

for item in evidence_results:

    result = item["result"]

    counts[result] = (
        counts.get(result, 0) + 1
    )


print(
    "\n===== LEDGERPILOT EVIDENCE ENGINE ====="
)

for result, count in counts.items():

    print(
        f"{result}: {count}"
    )


print(
    f"\nExceptions with evidence: "
    f"{len(evidence_results)}"
)

print(
    "\n✅ Evidence generation completed!"
)

print(
    "📁 Saved to: "
    "data/evidence_results.json"
)