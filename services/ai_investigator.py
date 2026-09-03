import csv
import json
import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


# =========================================================
# SAFE LOCAL FALLBACK
# =========================================================

def fallback_investigation(transaction):

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

    # ---------------------------------------------
    # Missing settlement
    # ---------------------------------------------

    if result == "MISSING_SETTLEMENT":

        return {
            "transaction_id": transaction["transaction_id"],
            "diagnosis": (
                "Successful payment has no matching "
                "bank settlement"
            ),
            "reason": (
                f"Payment of ₹{payment_amount:.2f} exists, "
                "but no corresponding bank settlement "
                "record was found."
            ),
            "confidence": 0.95,
            "recommended_action": (
                "Investigate settlement status and "
                "payout records"
            ),
            "risk": "HIGH",
            "needs_human_review": True,
            "source": "fallback"
        }


    # ---------------------------------------------
    # Partial settlement
    # ---------------------------------------------

    if result == "PARTIAL_SETTLEMENT":

        settled_percentage = (
            bank_amount / payment_amount * 100
            if payment_amount > 0
            else 0
        )

        return {
            "transaction_id": transaction["transaction_id"],
            "diagnosis": (
                "Partial settlement detected"
            ),
            "reason": (
                f"₹{bank_amount:.2f} was credited against "
                f"a payment of ₹{payment_amount:.2f}. "
                f"Approximately {settled_percentage:.1f}% "
                "was settled."
            ),
            "confidence": 0.97,
            "recommended_action": (
                "Verify settlement schedule and "
                "remaining payout"
            ),
            "risk": "HIGH",
            "needs_human_review": True,
            "source": "fallback"
        }


    # ---------------------------------------------
    # Duplicate settlement
    # ---------------------------------------------

    if result == "DUPLICATE_SETTLEMENT":

        return {
            "transaction_id": transaction["transaction_id"],
            "diagnosis": (
                "Duplicate settlement records detected"
            ),
            "reason": (
                f"Multiple bank records were found for "
                f"transaction {transaction['transaction_id']}. "
                f"Combined bank credit is ₹{bank_amount:.2f}."
            ),
            "confidence": 0.98,
            "recommended_action": (
                "Investigate duplicate settlement "
                "before reconciliation"
            ),
            "risk": "HIGH",
            "needs_human_review": True,
            "source": "fallback"
        }


    # ---------------------------------------------
    # Amount mismatch
    # ---------------------------------------------

    if result == "AMOUNT_MISMATCH":

        absolute_difference = abs(
            difference
        )

        if absolute_difference <= 100:

            return {
                "transaction_id": transaction["transaction_id"],
                "diagnosis": (
                    "Possible processing fee or "
                    "settlement adjustment"
                ),
                "reason": (
                    f"Payment is ₹{payment_amount:.2f} "
                    f"while the bank credit is "
                    f"₹{bank_amount:.2f}, a difference "
                    f"of ₹{absolute_difference:.2f}."
                ),
                "confidence": 0.90,
                "recommended_action": (
                    "Verify applicable fee and reconcile"
                ),
                "risk": "LOW",
                "needs_human_review": False,
                "source": "fallback"
            }

        return {
            "transaction_id": transaction["transaction_id"],
            "diagnosis": (
                "Unusual settlement amount difference"
            ),
            "reason": (
                f"Payment and bank settlement differ by "
                f"₹{absolute_difference:.2f}, which exceeds "
                "the normal fee-adjustment threshold."
            ),
            "confidence": 0.75,
            "recommended_action": (
                "Escalate to finance team for investigation"
            ),
            "risk": "HIGH",
            "needs_human_review": True,
            "source": "fallback"
        }


    # ---------------------------------------------
    # Unexpected settlement
    # ---------------------------------------------

    if result == "UNEXPECTED_SETTLEMENT":

        return {
            "transaction_id": transaction["transaction_id"],
            "diagnosis": (
                "Settlement detected for a failed payment"
            ),
            "reason": (
                f"A payment marked as FAILED has a bank "
                f"credit of ₹{bank_amount:.2f}."
            ),
            "confidence": 0.98,
            "recommended_action": (
                "Investigate transaction state and "
                "settlement records"
            ),
            "risk": "HIGH",
            "needs_human_review": True,
            "source": "fallback"
        }


    # ---------------------------------------------
    # Unknown exception
    # ---------------------------------------------

    return {
        "transaction_id": transaction["transaction_id"],
        "diagnosis": "Unknown reconciliation exception",
        "reason": (
            "The transaction type is not recognized "
            "by the investigation engine."
        ),
        "confidence": 0.50,
        "recommended_action": (
            "Manual investigation required"
        ),
        "risk": "HIGH",
        "needs_human_review": True,
        "source": "fallback"
    }


# =========================================================
# GEMINI BATCH INVESTIGATION
# =========================================================

def build_prompt(transactions):

    cases = []

    for transaction in transactions:

        payment_amount = float(
            transaction["payment_amount"]
        )

        bank_amount = float(
            transaction["bank_amount"]
        )

        cases.append({
            "transaction_id":
                transaction["transaction_id"],

            "payment_amount":
                payment_amount,

            "bank_amount":
                bank_amount,

            "difference":
                round(
                    payment_amount - bank_amount,
                    2
                ),

            "result":
                transaction["result"],

            "diagnosis":
                transaction["diagnosis"],

            "recommendation":
                transaction["recommendation"]
        })

    return f"""
You are LedgerPilot, an AI finance reconciliation investigator.

Analyze every exception in the dataset.

Use ONLY the supplied evidence.

Return ONLY a valid JSON array.

Each item MUST contain:

{{
  "transaction_id": "string",
  "diagnosis": "string",
  "reason": "string",
  "confidence": 0.0,
  "recommended_action": "string",
  "risk": "LOW | MEDIUM | HIGH",
  "needs_human_review": true
}}

Rules:
- Do not invent information.
- Do not claim money was recovered.
- Do not authorize payments, refunds, transfers,
  or other financial transactions.
- confidence must be between 0 and 1.
- Missing settlements should require human review.
- Partial settlements should require human review.
- Duplicate settlements should require human review.
- Large or uncertain discrepancies should be HIGH risk.
- Base every decision on the provided evidence.

Exceptions:

{json.dumps(cases, indent=2)}
"""


def investigate_batch(transactions):

    prompt = build_prompt(
        transactions
    )

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt
    )

    text = interaction.output_text.strip()

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    return json.loads(text)


# =========================================================
# LOAD DATA
# =========================================================

with open(
    "data/diagnosed_transactions.csv",
    newline="",
    encoding="utf-8"
) as file:

    all_transactions = list(
        csv.DictReader(file)
    )


exceptions = [
    transaction
    for transaction in all_transactions
    if transaction["result"] in [
        "MISSING_SETTLEMENT",
        "AMOUNT_MISMATCH",
        "PARTIAL_SETTLEMENT",
        "DUPLICATE_SETTLEMENT",
        "UNEXPECTED_SETTLEMENT"
    ]
]


print(
    "\n===== LEDGERPILOT AI INVESTIGATOR ====="
)

print(
    f"Exceptions to investigate: "
    f"{len(exceptions)}"
)


investigations = []


# =========================================================
# TRY GEMINI
# =========================================================

try:

    print(
        "\nAttempting ONE Gemini batch request..."
    )

    ai_results = investigate_batch(
        exceptions
    )

    if not isinstance(
        ai_results,
        list
    ):

        raise ValueError(
            "Gemini response is not a JSON array."
        )


    for result in ai_results:

        required_fields = [
            "transaction_id",
            "diagnosis",
            "reason",
            "confidence",
            "recommended_action",
            "risk",
            "needs_human_review"
        ]

        for field in required_fields:

            if field not in result:

                raise ValueError(
                    f"Missing field: {field}"
                )

        confidence = float(
            result["confidence"]
        )

        if not 0 <= confidence <= 1:

            raise ValueError(
                "Invalid confidence value."
            )

        if result["risk"] not in [
            "LOW",
            "MEDIUM",
            "HIGH"
        ]:

            raise ValueError(
                "Invalid risk value."
            )

        result["source"] = "gemini"

        investigations.append(
            result
        )


    print(
        "✅ Gemini batch investigation succeeded!"
    )


# =========================================================
# FALLBACK
# =========================================================

except Exception as error:

    print(
        "\n⚠️ Gemini unavailable."
    )

    print(
        f"Reason: {error}"
    )

    print(
        "Using safe deterministic fallback."
    )

    investigations = [
        fallback_investigation(
            transaction
        )
        for transaction in exceptions
    ]


# =========================================================
# SAVE
# =========================================================

with open(
    "data/real_ai_investigations.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        investigations,
        file,
        indent=4
    )


# =========================================================
# SUMMARY
# =========================================================

source_counts = {}

risk_counts = {}

human_review_count = 0


for result in investigations:

    source = result["source"]

    source_counts[source] = (
        source_counts.get(
            source,
            0
        ) + 1
    )

    risk = result["risk"]

    risk_counts[risk] = (
        risk_counts.get(
            risk,
            0
        ) + 1
    )

    if result["needs_human_review"]:

        human_review_count += 1


print(
    "\n===== INVESTIGATION SUMMARY ====="
)

print(
    f"Total investigations: "
    f"{len(investigations)}"
)

print(
    f"Human review required: "
    f"{human_review_count}"
)

print(
    "\nSources:"
)

for source, count in source_counts.items():

    print(
        f"{source}: {count}"
    )

print(
    "\nRisk:"
)

for risk, count in risk_counts.items():

    print(
        f"{risk}: {count}"
    )


print(
    "\n✅ Investigation pipeline completed!"
)

print(
    "📁 Saved to: "
    "data/real_ai_investigations.json"
)