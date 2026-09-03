import csv


def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


transactions = load_csv(
    "data/reconciliation.csv"
)

diagnosed = []


for transaction in transactions:

    transaction_id = transaction["transaction_id"]

    payment_amount = float(
        transaction["payment_amount"]
    )

    bank_amount = float(
        transaction["bank_amount"]
    )

    result = transaction["result"]

    difference = round(
        payment_amount - bank_amount,
        2
    )


    # ==========================================
    # Exact match
    # ==========================================

    if result == "MATCHED":

        diagnosis = "Payment fully reconciled"
        confidence = 0.99
        recommendation = "No action required"
        priority = "NONE"


    # ==========================================
    # Failed payment
    # ==========================================

    elif result == "FAILED_PAYMENT":

        diagnosis = (
            "Payment failed; no settlement expected"
        )

        confidence = 0.99
        recommendation = "No settlement action required"
        priority = "NONE"


    # ==========================================
    # Missing settlement
    # ==========================================

    elif result == "MISSING_SETTLEMENT":

        diagnosis = (
            "Successful payment has no matching "
            "bank settlement"
        )

        confidence = 0.95
        recommendation = (
            "Investigate settlement status "
            "and payout records"
        )

        priority = "HIGH"


    # ==========================================
    # Processing fee / amount mismatch
    # ==========================================

    elif result == "AMOUNT_MISMATCH":

        absolute_difference = abs(difference)

        if absolute_difference <= 100:

            diagnosis = (
                "Likely processing fee or "
                "settlement adjustment"
            )

            confidence = 0.90

            recommendation = (
                "Verify applicable fee "
                "and reconcile"
            )

            priority = "LOW"

        else:

            diagnosis = (
                "Unusual settlement amount difference"
            )

            confidence = 0.75

            recommendation = (
                "Escalate to finance team "
                "for investigation"
            )

            priority = "HIGH"


    # ==========================================
    # Partial settlement
    # ==========================================

    elif result == "PARTIAL_SETTLEMENT":

        settled_percentage = (
            bank_amount / payment_amount * 100
            if payment_amount > 0
            else 0
        )

        diagnosis = (
            f"Partial settlement detected; "
            f"approximately {settled_percentage:.1f}% "
            f"of the payment was credited"
        )

        confidence = 0.97

        recommendation = (
            "Verify settlement schedule and "
            "check for remaining payout"
        )

        priority = "HIGH"


    # ==========================================
    # Duplicate settlement
    # ==========================================

    elif result == "DUPLICATE_SETTLEMENT":

        diagnosis = (
            "Multiple bank records found for "
            "the same transaction"
        )

        confidence = 0.98

        recommendation = (
            "Investigate duplicate settlement "
            "before reconciliation"
        )

        priority = "HIGH"


    # ==========================================
    # Unknown result
    # ==========================================

    else:

        diagnosis = (
            "Unknown reconciliation exception"
        )

        confidence = 0.50

        recommendation = (
            "Manual investigation required"
        )

        priority = "HIGH"


    diagnosed.append({
        "transaction_id": transaction_id,
        "payment_amount": payment_amount,
        "bank_amount": bank_amount,
        "result": result,
        "diagnosis": diagnosis,
        "confidence": confidence,
        "recommendation": recommendation,
        "priority": priority
    })


# ==========================================
# Save diagnosis results
# ==========================================

with open(
    "data/diagnosed_transactions.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "transaction_id",
        "payment_amount",
        "bank_amount",
        "result",
        "diagnosis",
        "confidence",
        "recommendation",
        "priority"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(diagnosed)


# ==========================================
# Summary
# ==========================================

counts = {}

for row in diagnosed:

    result = row["result"]

    counts[result] = (
        counts.get(result, 0) + 1
    )


print(
    "\n===== LEDGERPILOT DIAGNOSIS ====="
)

for result, count in counts.items():

    print(
        f"{result}: {count}"
    )


print(
    "\n✅ Diagnosis completed!"
)

print(
    "📁 Saved to: "
    "data/diagnosed_transactions.csv"
)