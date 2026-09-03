import csv
import os


# =========================================================
# Load CSV helper
# =========================================================

def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


# =========================================================
# Load existing payment data
# =========================================================

payments = load_csv(
    "data/payments.csv"
)


# =========================================================
# Create deliberately difficult test cases
# =========================================================

adversarial_cases = [
    {
        "transaction_id": "ADV001",
        "payment_amount": 5000,
        "bank_amount": 4950,
        "result_expected": "AMOUNT_MISMATCH"
    },
    {
        "transaction_id": "ADV002",
        "payment_amount": 5000,
        "bank_amount": 2500,
        "result_expected": "PARTIAL_SETTLEMENT"
    },
    {
        "transaction_id": "ADV003",
        "payment_amount": 9999,
        "bank_amount": 0,
        "result_expected": "MISSING_SETTLEMENT"
    },
    {
        "transaction_id": "ADV004",
        "payment_amount": 999,
        "bank_amount": 1998,
        "result_expected": "DUPLICATE_SETTLEMENT"
    },
    {
        "transaction_id": "ADV005",
        "payment_amount": 799,
        "bank_amount": 0,
        "result_expected": "MISSING_SETTLEMENT"
    },
    {
        "transaction_id": "ADV006",
        "payment_amount": 2499,
        "bank_amount": 100,
        "result_expected": "PARTIAL_SETTLEMENT"
    },
    {
        "transaction_id": "ADV007",
        "payment_amount": 1000,
        "bank_amount": 990,
        "result_expected": "AMOUNT_MISMATCH"
    },
    {
        "transaction_id": "ADV008",
        "payment_amount": 9999,
        "bank_amount": 9999,
        "result_expected": "MATCHED"
    }
]


# =========================================================
# Create adversarial bank statement
# =========================================================

bank_records = []


for case in adversarial_cases:

    transaction_id = case["transaction_id"]

    expected = case["result_expected"]

    payment_amount = case["payment_amount"]
    bank_amount = case["bank_amount"]


    if expected == "MISSING_SETTLEMENT":

        # Intentionally no bank record
        continue


    if expected == "DUPLICATE_SETTLEMENT":

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": payment_amount,
            "status": "CREDITED",
            "scenario": "NORMAL"
        })

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": payment_amount,
            "status": "DUPLICATE",
            "scenario": "DUPLICATE"
        })

        continue


    if expected == "PARTIAL_SETTLEMENT":

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": bank_amount,
            "status": "PARTIAL",
            "scenario": "PARTIAL_SETTLEMENT"
        })

        continue


    if expected == "AMOUNT_MISMATCH":

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": bank_amount,
            "status": "CREDITED",
            "scenario": "PROCESSING_FEE"
        })

        continue


    if expected == "MATCHED":

        bank_records.append({
            "transaction_id": transaction_id,
            "bank_amount": bank_amount,
            "status": "CREDITED",
            "scenario": "NORMAL"
        })


# =========================================================
# Save adversarial cases
# =========================================================

os.makedirs(
    "data",
    exist_ok=True
)


with open(
    "data/adversarial_cases.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:

    fieldnames = [
        "transaction_id",
        "payment_amount",
        "expected_result"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for case in adversarial_cases:

        writer.writerow({
            "transaction_id":
                case["transaction_id"],

            "payment_amount":
                case["payment_amount"],

            "expected_result":
                case["result_expected"]
        })


print(
    "\n===== ADVERSARIAL TEST SUITE ====="
)

print(
    f"Test cases created: "
    f"{len(adversarial_cases)}"
)

print(
    "\nCases:"
)

for case in adversarial_cases:

    print(
        f"{case['transaction_id']} → "
        f"{case['result_expected']}"
    )


print(
    "\n✅ Adversarial dataset created!"
)

print(
    "📁 Saved to: data/adversarial_cases.csv"
)

print(
    "\nNext we will run these cases "
    "through the reconciliation engine."
)