import csv
from collections import defaultdict


def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


# =========================================================
# Load adversarial ground truth
# =========================================================

cases = load_csv(
    "data/adversarial_cases.csv"
)


# =========================================================
# Reconstruct the bank records used by the tests
# =========================================================

bank_records = [
    {
        "transaction_id": "ADV001",
        "bank_amount": 4950.0,
        "status": "CREDITED"
    },
    {
        "transaction_id": "ADV002",
        "bank_amount": 2500.0,
        "status": "PARTIAL"
    },
    # ADV003 intentionally missing

    {
        "transaction_id": "ADV004",
        "bank_amount": 999.0,
        "status": "CREDITED"
    },
    {
        "transaction_id": "ADV004",
        "bank_amount": 999.0,
        "status": "DUPLICATE"
    },

    # ADV005 intentionally missing

    {
        "transaction_id": "ADV006",
        "bank_amount": 100.0,
        "status": "PARTIAL"
    },
    {
        "transaction_id": "ADV007",
        "bank_amount": 990.0,
        "status": "CREDITED"
    },
    {
        "transaction_id": "ADV008",
        "bank_amount": 9999.0,
        "status": "CREDITED"
    }
]


# =========================================================
# Group bank records by transaction ID
# =========================================================

bank_lookup = defaultdict(list)

for record in bank_records:

    bank_lookup[
        record["transaction_id"]
    ].append(record)


# =========================================================
# Run reconciliation logic
# =========================================================

predictions = []


for case in cases:

    transaction_id = case[
        "transaction_id"
    ]

    payment_amount = float(
        case["payment_amount"]
    )

    matching_records = bank_lookup.get(
        transaction_id,
        []
    )


    # ---------------------------------------------
    # Missing settlement
    # ---------------------------------------------

    if not matching_records:

        predicted = "MISSING_SETTLEMENT"


    # ---------------------------------------------
    # Duplicate settlement
    # ---------------------------------------------

    elif len(matching_records) > 1:

        predicted = "DUPLICATE_SETTLEMENT"


    # ---------------------------------------------
    # Single bank record
    # ---------------------------------------------

    else:

        record = matching_records[0]

        bank_amount = float(
            record["bank_amount"]
        )

        status = record["status"]


        if status == "PARTIAL":

            predicted = "PARTIAL_SETTLEMENT"

        elif payment_amount == bank_amount:

            predicted = "MATCHED"

        else:

            predicted = "AMOUNT_MISMATCH"


    predictions.append({
        "transaction_id":
            transaction_id,

        "expected":
            case["expected_result"],

        "predicted":
            predicted
    })


# =========================================================
# Compare results
# =========================================================

correct = 0
incorrect = 0


print(
    "\n===== ADVERSARIAL TEST RESULTS ====="
)


for result in predictions:

    expected = result["expected"]
    predicted = result["predicted"]

    if expected == predicted:

        status = "✅ PASS"
        correct += 1

    else:

        status = "❌ FAIL"
        incorrect += 1

    print(
        f"{result['transaction_id']} | "
        f"Expected: {expected} | "
        f"Predicted: {predicted} | "
        f"{status}"
    )


# =========================================================
# Metrics
# =========================================================

total = len(predictions)

accuracy = (
    correct / total * 100
    if total > 0
    else 0
)


print(
    "\n===== ADVERSARIAL SUMMARY ====="
)

print(
    f"Total tests: {total}"
)

print(
    f"Passed: {correct}"
)

print(
    f"Failed: {incorrect}"
)

print(
    f"Accuracy: {accuracy:.2f}%"
)


if incorrect == 0:

    print(
        "\n✅ All adversarial tests passed!"
    )

else:

    print(
        "\n⚠️ Some adversarial tests failed."
    )