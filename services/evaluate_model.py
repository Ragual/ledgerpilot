import csv
from collections import Counter


def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


# =========================================================
# Load independent ground truth and predictions
# =========================================================

ground_truth = load_csv(
    "data/ground_truth.csv"
)

predictions = load_csv(
    "data/reconciliation.csv"
)


# Create lookup tables
ground_truth_lookup = {
    row["transaction_id"]: row["ground_truth"]
    for row in ground_truth
}

prediction_lookup = {
    row["transaction_id"]: row["result"]
    for row in predictions
}


# =========================================================
# Convert detailed labels into exception / non-exception
# =========================================================

exception_types = {
    "AMOUNT_MISMATCH",
    "PARTIAL_SETTLEMENT",
    "MISSING_SETTLEMENT",
    "DUPLICATE_SETTLEMENT",
    "UNEXPECTED_SETTLEMENT"
}


true_positive = 0
true_negative = 0
false_positive = 0
false_negative = 0


# =========================================================
# Evaluate each transaction
# =========================================================

for transaction_id, actual_label in ground_truth_lookup.items():

    predicted_label = prediction_lookup.get(
        transaction_id
    )

    actual_exception = (
        actual_label in exception_types
    )

    predicted_exception = (
        predicted_label in exception_types
    )


    if predicted_exception and actual_exception:
        true_positive += 1

    elif (
        not predicted_exception
        and not actual_exception
    ):
        true_negative += 1

    elif predicted_exception and not actual_exception:
        false_positive += 1

    elif (
        not predicted_exception
        and actual_exception
    ):
        false_negative += 1


# =========================================================
# Binary classification metrics
# =========================================================

precision = (
    true_positive /
    (true_positive + false_positive)
    if (true_positive + false_positive) > 0
    else 0
)

recall = (
    true_positive /
    (true_positive + false_negative)
    if (true_positive + false_negative) > 0
    else 0
)

f1_score = (
    2 * precision * recall /
    (precision + recall)
    if (precision + recall) > 0
    else 0
)

accuracy = (
    (true_positive + true_negative) /
    len(ground_truth)
    if ground_truth
    else 0
)


# =========================================================
# Detailed label accuracy
# =========================================================

correct_labels = 0

for transaction_id, actual_label in ground_truth_lookup.items():

    predicted_label = prediction_lookup.get(
        transaction_id
    )

    if predicted_label == actual_label:
        correct_labels += 1


label_accuracy = (
    correct_labels /
    len(ground_truth)
    if ground_truth
    else 0
)


# =========================================================
# Confusion matrix
# =========================================================

print(
    "\n===== LEDGERPILOT INDEPENDENT EVALUATION ====="
)

print(
    f"\nTotal records: "
    f"{len(ground_truth)}"
)

print(
    "\n===== EXCEPTION DETECTION ====="
)

print(
    f"True positives: "
    f"{true_positive}"
)

print(
    f"True negatives: "
    f"{true_negative}"
)

print(
    f"False positives: "
    f"{false_positive}"
)

print(
    f"False negatives: "
    f"{false_negative}"
)


print(
    "\n===== BINARY METRICS ====="
)

print(
    f"Accuracy:  "
    f"{accuracy * 100:.2f}%"
)

print(
    f"Precision: "
    f"{precision * 100:.2f}%"
)

print(
    f"Recall:    "
    f"{recall * 100:.2f}%"
)

print(
    f"F1 Score:  "
    f"{f1_score * 100:.2f}%"
)


print(
    "\n===== EXACT EXCEPTION TYPE MATCH ====="
)

print(
    f"Correct detailed labels: "
    f"{correct_labels}/{len(ground_truth)}"
)

print(
    f"Detailed label accuracy: "
    f"{label_accuracy * 100:.2f}%"
)


# =========================================================
# Ground-truth distribution
# =========================================================

actual_counts = Counter(
    row["ground_truth"]
    for row in ground_truth
)


predicted_counts = Counter(
    row["result"]
    for row in predictions
)


print(
    "\n===== GROUND TRUTH DISTRIBUTION ====="
)

for label, count in actual_counts.items():

    print(
        f"{label}: {count}"
    )


print(
    "\n===== PREDICTED DISTRIBUTION ====="
)

for label, count in predicted_counts.items():

    print(
        f"{label}: {count}"
    )


print(
    "\n✅ Independent evaluation completed!"
)