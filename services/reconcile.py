import csv
from collections import defaultdict


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

bank_records = load_csv(
    "data/bank_statement.csv"
)


# Group bank records by transaction ID
bank_lookup = defaultdict(list)

for row in bank_records:

    bank_lookup[
        row["transaction_id"]
    ].append(row)


results = []


for payment in payments:

    transaction_id = payment["transaction_id"]

    payment_amount = float(
        payment["amount"]
    )

    payment_status = payment["status"]

    matching_bank_records = bank_lookup.get(
        transaction_id,
        []
    )


    # ==========================================
    # Failed payment
    # ==========================================

    if payment_status == "FAILED":

        if matching_bank_records:

            result = "UNEXPECTED_SETTLEMENT"

            bank_amount = sum(
                float(row["bank_amount"])
                for row in matching_bank_records
            )

        else:

            result = "FAILED_PAYMENT"

            bank_amount = 0.0


    # ==========================================
    # Successful payment
    # ==========================================

    else:

        # No bank record
        if not matching_bank_records:

            result = "MISSING_SETTLEMENT"
            bank_amount = 0.0


        # Multiple bank records
        elif len(matching_bank_records) > 1:

            bank_amount = sum(
                float(row["bank_amount"])
                for row in matching_bank_records
            )

            result = "DUPLICATE_SETTLEMENT"


        # Exactly one bank record
        else:

            bank_amount = float(
                matching_bank_records[0]["bank_amount"]
            )

            bank_status = matching_bank_records[0][
                "status"
            ]

            # Partial settlement
            if bank_status == "PARTIAL":

                result = "PARTIAL_SETTLEMENT"

            # Normal exact match
            elif payment_amount == bank_amount:

                result = "MATCHED"

            # Amount mismatch
            else:

                result = "AMOUNT_MISMATCH"


    results.append({
        "transaction_id": transaction_id,
        "payment_amount": payment_amount,
        "bank_amount": round(
            bank_amount,
            2
        ),
        "result": result
    })


# ==========================================
# Save reconciliation results
# ==========================================

with open(
    "data/reconciliation.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "transaction_id",
        "payment_amount",
        "bank_amount",
        "result"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(results)


# ==========================================
# Summary
# ==========================================

counts = {}

for row in results:

    result = row["result"]

    counts[result] = (
        counts.get(result, 0) + 1
    )


print(
    "\n===== LEDGERPILOT RECONCILIATION ====="
)

for result, count in counts.items():

    print(
        f"{result}: {count}"
    )


print(
    f"\nTotal transactions: {len(results)}"
)

print(
    "\n✅ Reconciliation completed!"
)

print(
    "📁 Saved to: data/reconciliation.csv"
)