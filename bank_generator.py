import csv
import random


# =========================================================
# Load payments
# =========================================================

with open(
    "data/payments.csv",
    newline="",
    encoding="utf-8"
) as file:
    payments = list(csv.DictReader(file))


bank_records = []
ground_truth = []


# =========================================================
# Generate bank scenarios + independent ground truth
# =========================================================

for payment in payments:

    transaction_id = payment["transaction_id"]
    amount = float(payment["amount"])
    status = payment["status"]


    # -----------------------------------------------------
    # Failed payment
    # -----------------------------------------------------

    if status == "FAILED":

        # Normally nothing should reach the bank
        ground_truth.append({
            "transaction_id": transaction_id,
            "ground_truth": "FAILED_PAYMENT"
        })

        continue


    # -----------------------------------------------------
    # Successful payment
    # -----------------------------------------------------

    scenario = random.random()


    # =====================================================
    # NORMAL SETTLEMENT
    # =====================================================

    if scenario < 0.70:

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": amount,
            "status": "CREDITED",
            "scenario": "NORMAL"
        })

        ground_truth.append({
            "transaction_id": transaction_id,
            "ground_truth": "MATCHED"
        })


    # =====================================================
    # PROCESSING FEE
    # =====================================================

    elif scenario < 0.82:

        fee = random.choice([
            10,
            20,
            50,
            100
        ])

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": round(
                amount - fee,
                2
            ),
            "status": "CREDITED",
            "scenario": "PROCESSING_FEE"
        })

        ground_truth.append({
            "transaction_id": transaction_id,
            "ground_truth": "AMOUNT_MISMATCH"
        })


    # =====================================================
    # PARTIAL SETTLEMENT
    # =====================================================

    elif scenario < 0.90:

        percentage = random.choice([
            0.25,
            0.50,
            0.75
        ])

        partial_amount = round(
            amount * percentage,
            2
        )

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": partial_amount,
            "status": "PARTIAL",
            "scenario": "PARTIAL_SETTLEMENT"
        })

        ground_truth.append({
            "transaction_id": transaction_id,
            "ground_truth": "PARTIAL_SETTLEMENT"
        })


    # =====================================================
    # MISSING SETTLEMENT
    # =====================================================

    elif scenario < 0.96:

        # Intentionally no bank record
        ground_truth.append({
            "transaction_id": transaction_id,
            "ground_truth": "MISSING_SETTLEMENT"
        })


    # =====================================================
    # DUPLICATE SETTLEMENT
    # =====================================================

    else:

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": amount,
            "status": "CREDITED",
            "scenario": "NORMAL"
        })

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": amount,
            "status": "DUPLICATE",
            "scenario": "DUPLICATE"
        })

        ground_truth.append({
            "transaction_id": transaction_id,
            "ground_truth": "DUPLICATE_SETTLEMENT"
        })


# =========================================================
# Save bank statement
# =========================================================

with open(
    "data/bank_statement.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "transaction_id",
        "bank_amount",
        "status",
        "scenario"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(bank_records)


# =========================================================
# Save independent ground truth
# =========================================================

with open(
    "data/ground_truth.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "transaction_id",
        "ground_truth"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(ground_truth)


# =========================================================
# Print summary
# =========================================================

ground_truth_counts = {}

for row in ground_truth:

    scenario = row["ground_truth"]

    ground_truth_counts[scenario] = (
        ground_truth_counts.get(
            scenario,
            0
        ) + 1
    )


print(
    "\n===== DATA GENERATION COMPLETE ====="
)

print(
    f"Payments generated: {len(payments)}"
)

print(
    f"Bank records generated: {len(bank_records)}"
)

print(
    "\nGround truth:"
)

for scenario, count in ground_truth_counts.items():

    print(
        f"{scenario}: {count}"
    )


print(
    "\n✅ Bank statement created!"
)

print(
    "📁 data/bank_statement.csv"
)

print(
    "📁 data/ground_truth.csv"
)