import csv
import json


# =========================================================
# Guardrail configuration
# =========================================================

MIN_AI_CONFIDENCE = 0.80
MAX_AUTO_MISMATCH_DIFFERENCE = 100.00


# =========================================================
# Load helpers
# =========================================================

def load_csv(filename):
    with open(
        filename,
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def load_json(filename):
    with open(
        filename,
        encoding="utf-8"
    ) as file:
        return json.load(file)


# =========================================================
# Guardrail engine
# =========================================================

def evaluate_decision(transaction, ai_result):

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

    result_type = transaction["result"]

    risk = ai_result.get(
        "risk",
        "HIGH"
    )

    confidence = float(
        ai_result.get(
            "confidence",
            0
        )
    )

    recommendation = ai_result.get(
        "recommended_action",
        ""
    )

    # Safe defaults
    decision = "HUMAN_REVIEW"
    allowed_action = "Manual investigation"

    reasons = []


    # =====================================================
    # Rule 1: Missing settlement
    # =====================================================

    if result_type == "MISSING_SETTLEMENT":

        decision = "HUMAN_REVIEW"
        allowed_action = "Investigate settlement"

        reasons.append(
            "Settlement record is missing"
        )


    # =====================================================
    # Rule 2: Partial settlement
    # =====================================================

    elif result_type == "PARTIAL_SETTLEMENT":

        decision = "HUMAN_REVIEW"
        allowed_action = (
            "Verify remaining settlement"
        )

        reasons.append(
            "Only part of the payment was settled"
        )


    # =====================================================
    # Rule 3: Duplicate settlement
    # =====================================================

    elif result_type == "DUPLICATE_SETTLEMENT":

        decision = "HUMAN_REVIEW"
        allowed_action = (
            "Investigate duplicate settlement"
        )

        reasons.append(
            "Multiple settlement records exist "
            "for the same transaction"
        )


    # =====================================================
    # Rule 4: Unexpected settlement
    # =====================================================

    elif result_type == "UNEXPECTED_SETTLEMENT":

        decision = "BLOCK"
        allowed_action = (
            "No automatic financial action"
        )

        reasons.append(
            "Settlement exists for a failed payment"
        )


    # =====================================================
    # Rule 5: Amount mismatch
    # =====================================================

    elif result_type == "AMOUNT_MISMATCH":

        absolute_difference = abs(
            difference
        )

        if absolute_difference <= (
            MAX_AUTO_MISMATCH_DIFFERENCE
        ):

            decision = "AUTO_REVIEW"

            allowed_action = (
                "Verify fee and reconcile"
            )

            reasons.append(
                "Amount difference is within "
                "the approved threshold"
            )

        else:

            decision = "HUMAN_REVIEW"

            allowed_action = (
                "Investigate amount discrepancy"
            )

            reasons.append(
                f"Difference of ₹"
                f"{absolute_difference:.2f} "
                f"exceeds ₹"
                f"{MAX_AUTO_MISMATCH_DIFFERENCE:.2f} "
                "threshold"
            )


    # =====================================================
    # Rule 6: High risk always requires human review
    # =====================================================

    if risk == "HIGH":

        if result_type != "UNEXPECTED_SETTLEMENT":

            decision = "HUMAN_REVIEW"

            reasons.append(
                "AI classified the case as HIGH risk"
            )


    # =====================================================
    # Rule 7: Low confidence requires human review
    # =====================================================

    if confidence < MIN_AI_CONFIDENCE:

        decision = "HUMAN_REVIEW"

        allowed_action = (
            "Manual investigation"
        )

        reasons.append(
            f"AI confidence ({confidence:.2f}) "
            f"is below the required threshold "
            f"({MIN_AI_CONFIDENCE:.2f})"
        )


    # =====================================================
    # Rule 8: Never allow direct financial execution
    # =====================================================

    restricted_actions = [
        "transfer",
        "send money",
        "refund",
        "withdraw",
        "charge customer",
        "make payment"
    ]

    recommendation_lower = (
        recommendation.lower()
    )

    for restricted_action in restricted_actions:

        if restricted_action in recommendation_lower:

            decision = "BLOCK"

            allowed_action = (
                "No financial action permitted"
            )

            reasons.append(
                "AI recommendation contains "
                "a restricted financial action"
            )

            break


    # =====================================================
    # Fallback reason
    # =====================================================

    if not reasons:

        reasons.append(
            "No additional guardrail violations detected"
        )


    return {
        "transaction_id":
            transaction["transaction_id"],

        "decision":
            decision,

        "allowed_action":
            allowed_action,

        "risk":
            risk,

        "confidence":
            confidence,

        "difference":
            difference,

        "guardrail_reasons":
            reasons
    }


# =========================================================
# Load input data
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


guardrail_results = []


print(
    "\n===== LEDGERPILOT GUARDRAIL ENGINE ====="
)


for transaction in transactions:

    result_type = transaction["result"]

    if result_type not in exception_types:
        continue

    transaction_id = (
        transaction["transaction_id"]
    )

    ai_result = ai_lookup.get(
        transaction_id
    )


    # ---------------------------------------------
    # Safe behavior when AI output is unavailable
    # ---------------------------------------------

    if not ai_result:

        result = {
            "transaction_id":
                transaction_id,

            "decision":
                "HUMAN_REVIEW",

            "allowed_action":
                "Manual investigation",

            "risk":
                "HIGH",

            "confidence":
                0.0,

            "difference":
                round(
                    float(
                        transaction["payment_amount"]
                    )
                    -
                    float(
                        transaction["bank_amount"]
                    ),
                    2
                ),

            "guardrail_reasons": [
                "No valid AI investigation available"
            ]
        }

    else:

        result = evaluate_decision(
            transaction,
            ai_result
        )


    guardrail_results.append(
        result
    )


    print(
        f"\nTransaction: "
        f"{result['transaction_id']}"
    )

    print(
        f"Decision: "
        f"{result['decision']}"
    )

    print(
        f"Allowed action: "
        f"{result['allowed_action']}"
    )

    print(
        f"Risk: "
        f"{result['risk']}"
    )

    print(
        f"Confidence: "
        f"{result['confidence'] * 100:.1f}%"
    )

    print(
        "Reasons:"
    )

    for reason in result[
        "guardrail_reasons"
    ]:

        print(
            f"  ✓ {reason}"
        )


# =========================================================
# Save results
# =========================================================

with open(
    "data/guardrail_results.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        guardrail_results,
        file,
        indent=4
    )


# =========================================================
# Summary
# =========================================================

summary = {}

for result in guardrail_results:

    decision = result["decision"]

    summary[decision] = (
        summary.get(
            decision,
            0
        ) + 1
    )


print(
    "\n===== GUARDRAIL SUMMARY ====="
)

for decision in [
    "AUTO_REVIEW",
    "HUMAN_REVIEW",
    "BLOCK"
]:

    print(
        f"{decision}: "
        f"{summary.get(decision, 0)}"
    )


print(
    f"\nTotal exceptions evaluated: "
    f"{len(guardrail_results)}"
)

print(
    "\n✅ Guardrail evaluation completed!"
)

print(
    "📁 Saved to: "
    "data/guardrail_results.json"
)