import csv
import json
import os
import time
import urllib.request
import urllib.error

from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)

LLM_TIMEOUT_SECONDS = int(
    os.getenv("LLM_TIMEOUT_SECONDS", "120")
)

# 50 means:
# 111 exceptions -> 50 + 50 + 11
BATCH_SIZE = int(
    os.getenv("LLM_BATCH_SIZE", "50")
)

MAX_RETRIES = int(
    os.getenv("LLM_MAX_RETRIES", "3")
)

RETRY_BASE_SECONDS = float(
    os.getenv("LLM_RETRY_BASE_SECONDS", "2")
)


# ============================================================
# PATHS
# ============================================================

INPUT_FILE = "data/diagnosed_transactions.csv"
OUTPUT_FILE = "data/real_ai_investigations.json"


# ============================================================
# CUSTOM EXCEPTIONS
# ============================================================

class GeminiQuotaExceeded(Exception):
    """
    Raised when Gemini quota is exhausted.

    This is intentionally separate from normal transient
    errors because retrying an exhausted quota is useless.
    """
    pass


# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    """
    Convert a value to float safely.
    """

    try:
        if value is None:
            return 0.0

        value = str(value).strip()

        if not value:
            return 0.0

        return float(value)

    except (ValueError, TypeError):
        return 0.0


def normalize_text(value):
    """
    Normalize text for comparisons.
    """

    if value is None:
        return ""

    return str(value).strip().upper()


def normalize_priority(value):
    """
    Normalize priority values.
    """

    priority = normalize_text(value)

    if priority in {"CRITICAL", "HIGH"}:
        return "HIGH"

    if priority == "MEDIUM":
        return "MEDIUM"

    if priority == "LOW":
        return "LOW"

    if priority == "NONE":
        return "NONE"

    return ""


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

def load_transactions():
    """
    Load diagnosed transactions from CSV.

    CSV columns:

        transaction_id
        payment_amount
        bank_amount
        result
        diagnosis
        confidence
        recommendation
        priority

    Normal transactions are excluded:

        MATCHED
        FAILED_PAYMENT

    Everything else is treated as an exception.
    """

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    transactions = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise RuntimeError(
                "CSV does not contain headers."
            )

        print(
            f"CSV columns detected: {reader.fieldnames}"
        )

        for row in reader:

            result = normalize_text(
                row.get("result", "")
            )

            # ------------------------------------------------
            # Ignore normal transactions
            # ------------------------------------------------

            if result in {
                "MATCHED",
                "FAILED_PAYMENT"
            }:
                continue

            transaction = prepare_transaction(
                row
            )

            transactions.append(
                transaction
            )

    return transactions


# ============================================================
# DERIVE EXCEPTION TYPE
# ============================================================

def derive_exception_type(row):
    """
    Determine the exception type.

    The 'result' column is the primary source of truth.
    """

    result = normalize_text(
        row.get("result", "")
    )

    # --------------------------------------------------------
    # Exact result mappings
    # --------------------------------------------------------

    result_mapping = {
        "MISSING_SETTLEMENT":
            "MISSING_SETTLEMENT",

        "AMOUNT_MISMATCH":
            "AMOUNT_MISMATCH",

        "PARTIAL_SETTLEMENT":
            "PARTIAL_SETTLEMENT",

        "DUPLICATE_SETTLEMENT":
            "DUPLICATE_SETTLEMENT",

        "UNEXPECTED_SETTLEMENT":
            "UNEXPECTED_SETTLEMENT"
    }

    if result in result_mapping:
        return result_mapping[result]

    # --------------------------------------------------------
    # Fallback to diagnosis/recommendation text
    # --------------------------------------------------------

    diagnosis = normalize_text(
        row.get("diagnosis", "")
    )

    recommendation = normalize_text(
        row.get("recommendation", "")
    )

    combined = " ".join([
        result,
        diagnosis,
        recommendation
    ])

    # Missing settlement

    if "MISSING" in combined:
        return "MISSING_SETTLEMENT"

    # Partial settlement

    if "PARTIAL" in combined:
        return "PARTIAL_SETTLEMENT"

    # Duplicate settlement

    if "DUPLICATE" in combined:
        return "DUPLICATE_SETTLEMENT"

    # Unexpected settlement

    if "UNEXPECTED" in combined:
        return "UNEXPECTED_SETTLEMENT"

    # Amount mismatch

    if (
        "MISMATCH" in combined
        or "AMOUNT DIFFERENCE" in combined
    ):
        return "AMOUNT_MISMATCH"

    return "UNKNOWN_EXCEPTION"


# ============================================================
# PREPARE TRANSACTION
# ============================================================

def prepare_transaction(row):
    """
    Convert CSV row into a clean investigation object.
    """

    payment_amount = safe_float(
        row.get("payment_amount")
    )

    bank_amount = safe_float(
        row.get("bank_amount")
    )

    amount_difference = round(
        payment_amount - bank_amount,
        2
    )

    exception_type = derive_exception_type(
        row
    )

    return {
        "transaction_id": str(
            row.get(
                "transaction_id",
                ""
            )
        ).strip(),

        "payment_amount": payment_amount,

        "bank_amount": bank_amount,

        "amount_difference": amount_difference,

        "result": str(
            row.get(
                "result",
                ""
            )
        ).strip(),

        "exception_type": exception_type,

        "diagnosis": str(
            row.get(
                "diagnosis",
                ""
            )
        ).strip(),

        "confidence": safe_float(
            row.get("confidence")
        ),

        "recommendation": str(
            row.get(
                "recommendation",
                ""
            )
        ).strip(),

        "priority": str(
            row.get(
                "priority",
                ""
            )
        ).strip()
    }


# ============================================================
# DETERMINISTIC FALLBACK
# ============================================================

def deterministic_investigation(transaction):
    """
    Deterministic fallback used when Gemini is unavailable.

    IMPORTANT:
    This function preserves the original diagnosis,
    recommendation, confidence and priority from the
    diagnosis engine instead of blindly marking every
    exception as HIGH.
    """

    transaction_id = transaction.get(
        "transaction_id",
        ""
    )

    exception_type = transaction.get(
        "exception_type",
        "UNKNOWN_EXCEPTION"
    )

    payment_amount = transaction.get(
        "payment_amount",
        0.0
    )

    bank_amount = transaction.get(
        "bank_amount",
        0.0
    )

    amount_difference = transaction.get(
        "amount_difference",
        0.0
    )

    original_diagnosis = str(
        transaction.get(
            "diagnosis",
            ""
        )
    ).strip()

    original_recommendation = str(
        transaction.get(
            "recommendation",
            ""
        )
    ).strip()

    original_confidence = safe_float(
        transaction.get(
            "confidence"
        )
    )

    original_priority = normalize_priority(
        transaction.get(
            "priority",
            ""
        )
    )

    # --------------------------------------------------------
    # Diagnosis
    # --------------------------------------------------------

    if original_diagnosis:
        diagnosis = original_diagnosis

    else:

        diagnosis_map = {

            "MISSING_SETTLEMENT":
                "Settlement is missing.",

            "PARTIAL_SETTLEMENT":
                "Partial settlement detected.",

            "AMOUNT_MISMATCH":
                "Payment and bank settlement amounts differ.",

            "DUPLICATE_SETTLEMENT":
                "Potential duplicate settlement.",

            "UNEXPECTED_SETTLEMENT":
                "Unexpected settlement detected.",

            "UNKNOWN_EXCEPTION":
                "Exception requires investigation."
        }

        diagnosis = diagnosis_map.get(
            exception_type,
            "Exception requires investigation."
        )

    # --------------------------------------------------------
    # Reason
    # --------------------------------------------------------

    if exception_type == "MISSING_SETTLEMENT":

        reason = (
            f"Payment amount of "
            f"{payment_amount:.2f} has no corresponding "
            f"bank settlement."
        )

    elif exception_type == "PARTIAL_SETTLEMENT":

        reason = (
            f"Payment amount is "
            f"{payment_amount:.2f}, while bank settlement "
            f"is {bank_amount:.2f}. "
            f"Difference: {amount_difference:.2f}."
        )

    elif exception_type == "AMOUNT_MISMATCH":

        reason = (
            f"Payment amount: "
            f"{payment_amount:.2f}; "
            f"bank amount: "
            f"{bank_amount:.2f}; "
            f"difference: "
            f"{amount_difference:.2f}."
        )

    elif exception_type == "DUPLICATE_SETTLEMENT":

        reason = (
            "The transaction appears to have multiple "
            "settlement records."
        )

    elif exception_type == "UNEXPECTED_SETTLEMENT":

        reason = (
            "A bank settlement was detected that does not "
            "match the expected transaction."
        )

    else:

        if original_diagnosis:
            reason = original_diagnosis

        else:
            reason = (
                f"Transaction {transaction_id} was flagged "
                f"as {exception_type}."
            )

    # --------------------------------------------------------
    # Recommended action
    # --------------------------------------------------------

    if original_recommendation:

        recommended_action = (
            original_recommendation
        )

    else:

        action_map = {

            "MISSING_SETTLEMENT":
                "Verify settlement status with the payment "
                "processor and check for delayed settlement.",

            "PARTIAL_SETTLEMENT":
                "Reconcile the settlement difference and "
                "verify fees, adjustments, or partial captures.",

            "AMOUNT_MISMATCH":
                "Verify transaction amounts against processor "
                "settlement records and investigate the difference.",

            "DUPLICATE_SETTLEMENT":
                "Check settlement references and verify whether "
                "a duplicate settlement occurred.",

            "UNEXPECTED_SETTLEMENT":
                "Verify the settlement reference and investigate "
                "the source of the unexpected amount.",

            "UNKNOWN_EXCEPTION":
                "Review the transaction and verify settlement records."
        }

        recommended_action = action_map.get(
            exception_type,
            "Review the transaction and verify settlement records."
        )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    # Preserve the diagnosis engine's priority.

    if original_priority == "HIGH":

        risk = "HIGH"

    elif original_priority == "MEDIUM":

        risk = "MEDIUM"

    elif original_priority == "LOW":

        risk = "LOW"

    else:

        # Conservative default for unknown priority
        risk = "MEDIUM"

    # --------------------------------------------------------
    # Human review
    # --------------------------------------------------------

    # High-risk exceptions always require human review.
    #
    # Low-risk amount mismatches do not automatically require
    # human review because the diagnosis engine already marked
    # them as low priority.

    if risk == "HIGH":
        needs_human_review = True

    elif risk == "MEDIUM":
        needs_human_review = True

    else:
        needs_human_review = False

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if 0 < original_confidence <= 1:
        confidence = original_confidence

    else:
        confidence = 0.65

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {
        "transaction_id": transaction_id,

        "diagnosis": diagnosis,

        "reason": reason,

        "confidence": confidence,

        "recommended_action":
            recommended_action,

        "risk": risk,

        "needs_human_review":
            needs_human_review,

        "source":
            "deterministic_fallback"
    }


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_prompt(transactions):
    """
    Build Gemini investigation prompt.
    """

    transaction_json = json.dumps(
        transactions,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
You are the AI investigation engine for LedgerPilot,
a financial transaction reconciliation system.

You are given transactions that have ALREADY been identified
as exceptions.

Your job is to investigate each exception using ONLY the
evidence contained in the supplied transaction data.

Do NOT invent:
- transaction information
- customer information
- settlement information
- processor information
- dates
- causes that are not supported by the evidence

For every transaction return EXACTLY these fields:

1. transaction_id
2. diagnosis
3. reason
4. confidence
5. recommended_action
6. risk
7. needs_human_review

Rules:

- Return exactly one result for every supplied transaction.
- Do not omit any transaction.
- Do not duplicate transaction IDs.
- confidence must be a number between 0 and 1.
- risk must be exactly one of:
  LOW
  MEDIUM
  HIGH
- needs_human_review must be true or false.

Important:

The supplied diagnosis, recommendation and priority are
evidence from the deterministic reconciliation engine.

Use them when appropriate.

Do not change a LOW priority exception to HIGH unless the
supplied transaction evidence clearly justifies doing so.

Do not change a HIGH priority exception to LOW without strong
evidence.

Investigation guidance:

MISSING_SETTLEMENT:
Determine why the expected settlement is missing.

PARTIAL_SETTLEMENT:
Explain the difference between expected payment and actual
bank settlement.

AMOUNT_MISMATCH:
Explain the amount difference using the supplied amounts.

DUPLICATE_SETTLEMENT:
Identify the potential duplicate and recommend verification.

UNEXPECTED_SETTLEMENT:
Explain why the settlement appears unexpected.

UNKNOWN_EXCEPTION:
Use the supplied diagnosis and recommendation as evidence
and explain what should be checked.

Prefer conservative conclusions.

If evidence is insufficient, explicitly say that human review
is required.

Return ONLY a valid JSON array.

Do not use markdown.
Do not wrap the JSON in ```.

Transactions:

{transaction_json}
"""

    return prompt


# ============================================================
# EXTRACT JSON ARRAY
# ============================================================

def extract_json_array(text):
    """
    Extract a JSON array from Gemini response.
    """

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown fences
    # --------------------------------------------------------

    if text.startswith("```"):

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip().startswith("```")
        ):
            lines = lines[:-1]

        text = "\n".join(
            lines
        ).strip()

    # --------------------------------------------------------
    # Direct JSON parse
    # --------------------------------------------------------

    try:

        parsed = json.loads(
            text
        )

        if isinstance(parsed, list):
            return parsed

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Find balanced JSON array
    # --------------------------------------------------------

    start = text.find("[")

    if start == -1:

        raise ValueError(
            "No JSON array found in Gemini response."
        )

    depth = 0
    in_string = False
    escape = False

    for index in range(
        start,
        len(text)
    ):

        char = text[index]

        if in_string:

            if escape:
                escape = False

            elif char == "\\":
                escape = True

            elif char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True

        elif char == "[":
            depth += 1

        elif char == "]":

            depth -= 1

            if depth == 0:

                candidate = text[
                    start:index + 1
                ]

                parsed = json.loads(
                    candidate
                )

                if not isinstance(
                    parsed,
                    list
                ):
                    raise ValueError(
                        "Extracted JSON is not an array."
                    )

                return parsed

    raise ValueError(
        "Could not extract a complete JSON array."
    )


# ============================================================
# VALIDATE GEMINI RESULTS
# ============================================================

def validate_llm_results(
    results,
    transactions
):
    """
    Validate Gemini response against input batch.
    """

    if not isinstance(
        results,
        list
    ):
        raise ValueError(
            "Gemini result is not a list."
        )

    expected_ids = [
        transaction[
            "transaction_id"
        ]
        for transaction in transactions
    ]

    actual_ids = [
        str(
            item.get(
                "transaction_id",
                ""
            )
        ).strip()

        for item in results

        if isinstance(
            item,
            dict
        )
    ]

    # --------------------------------------------------------
    # Count
    # --------------------------------------------------------

    if len(results) != len(
        transactions
    ):

        raise ValueError(
            f"Expected "
            f"{len(transactions)} results, "
            f"received "
            f"{len(results)}."
        )

    # --------------------------------------------------------
    # Duplicate IDs
    # --------------------------------------------------------

    if len(
        set(actual_ids)
    ) != len(actual_ids):

        raise ValueError(
            "Gemini returned duplicate "
            "transaction IDs."
        )

    # --------------------------------------------------------
    # Correct IDs
    # --------------------------------------------------------

    if set(actual_ids) != set(
        expected_ids
    ):

        raise ValueError(
            "Gemini returned incorrect "
            "transaction IDs."
        )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_fields = {
        "transaction_id",
        "diagnosis",
        "reason",
        "confidence",
        "recommended_action",
        "risk",
        "needs_human_review"
    }

    validated = []

    for item in results:

        if not isinstance(
            item,
            dict
        ):
            raise ValueError(
                "Gemini returned a "
                "non-object result."
            )

        missing = (
            required_fields
            - set(item.keys())
        )

        if missing:

            raise ValueError(
                f"Missing fields: "
                f"{missing}"
            )

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        try:

            confidence = float(
                item["confidence"]
            )

        except (
            ValueError,
            TypeError
        ):

            raise ValueError(
                "Invalid confidence value."
            )

        if not 0 <= confidence <= 1:

            raise ValueError(
                "Confidence must be "
                "between 0 and 1."
            )

        item["confidence"] = confidence

        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        risk = normalize_text(
            item["risk"]
        )

        if risk not in {
            "LOW",
            "MEDIUM",
            "HIGH"
        }:

            raise ValueError(
                f"Invalid risk: {risk}"
            )

        item["risk"] = risk

        # ----------------------------------------------------
        # Human review
        # ----------------------------------------------------

        if not isinstance(
            item[
                "needs_human_review"
            ],
            bool
        ):

            raise ValueError(
                "needs_human_review "
                "must be boolean."
            )

        # ----------------------------------------------------
        # Normalize transaction ID
        # ----------------------------------------------------

        item["transaction_id"] = str(
            item["transaction_id"]
        ).strip()

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        item["source"] = "gemini"

        validated.append(
            item
        )

    return validated


# ============================================================
# HTTP REQUEST
# ============================================================

def http_post_json(
    url,
    payload
):
    """
    Send JSON POST request using urllib.
    """

    body = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type":
                "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=LLM_TIMEOUT_SECONDS
        ) as response:

            response_body = (
                response
                .read()
                .decode(
                    "utf-8"
                )
            )

            return json.loads(
                response_body
            )

    except urllib.error.HTTPError as error:

        try:

            error_body = (
                error
                .read()
                .decode(
                    "utf-8",
                    errors="replace"
                )
            )

        except Exception:

            error_body = ""

        message = (
            f"HTTP {error.code}: "
            f"{error_body}"
        )

        # ----------------------------------------------------
        # CRITICAL:
        # Detect exhausted quota immediately.
        # Do NOT retry it.
        # ----------------------------------------------------

        upper_message = (
            message.upper()
        )

        quota_exhausted = (
            "QUOTA EXCEEDED"
            in upper_message

            or "FREE_TIER"
            in upper_message

            or "RESOURCE_EXHAUSTED"
            in upper_message

            or "GENERATE_CONTENT_FREE_TIER_REQUESTS"
            in upper_message

            or (
                error.code == 429
                and (
                    "CURRENT QUOTA"
                    in upper_message
                    or "LIMIT: 0"
                    in upper_message
                )
            )
        )

        if quota_exhausted:

            raise GeminiQuotaExceeded(
                message
            )

        raise RuntimeError(
            message
        )

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Network error: "
            f"{error.reason}"
        )

    except TimeoutError:

        raise RuntimeError(
            "Request timed out."
        )


# ============================================================
# QUOTA ERROR DETECTION
# ============================================================

def is_quota_exceeded_error(
    error
):
    """
    Detect whether an error means the Gemini quota
    has been exhausted.
    """

    message = str(
        error
    ).upper()

    quota_phrases = [
        "QUOTA EXCEEDED",
        "FREE_TIER",
        "RESOURCE_EXHAUSTED",
        "GENERATE_CONTENT_FREE_TIER_REQUESTS",
        "CURRENT QUOTA",
        "LIMIT: 0"
    ]

    return any(
        phrase in message
        for phrase in quota_phrases
    )


# ============================================================
# TRANSIENT ERROR DETECTION
# ============================================================

def is_transient_error(
    error
):
    """
    Determine whether an error is worth retrying.

    Quota exhaustion is NOT considered transient.
    """

    # --------------------------------------------------------
    # Never retry exhausted quota
    # --------------------------------------------------------

    if isinstance(
        error,
        GeminiQuotaExceeded
    ):
        return False

    if is_quota_exceeded_error(
        error
    ):
        return False

    message = str(
        error
    ).upper()

    # --------------------------------------------------------
    # HTTP transient codes
    # --------------------------------------------------------

    transient_codes = [
        "500",
        "502",
        "503",
        "504"
    ]

    for code in transient_codes:

        if code in message:
            return True

    # --------------------------------------------------------
    # Temporary errors
    # --------------------------------------------------------

    transient_messages = [
        "TIMEOUT",
        "TIMED OUT",
        "TEMPORARY",
        "CONNECTION RESET",
        "CONNECTION ABORTED",
        "NETWORK ERROR",
        "SERVICE UNAVAILABLE",
        "HIGH DEMAND",
        "RATE LIMIT"
    ]

    for phrase in transient_messages:

        if phrase in message:
            return True

    # --------------------------------------------------------
    # 429 that is NOT quota exhaustion
    # --------------------------------------------------------

    if "429" in message:

        return True

    return False


# ============================================================
# RETRY WRAPPER
# ============================================================

def call_with_retry(
    function,
    *args,
    **kwargs
):
    """
    Retry Gemini calls only for temporary failures.

    Quota exhaustion is never retried.
    """

    last_error = None

    delays = [
        RETRY_BASE_SECONDS,
        5,
        10
    ]

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            return function(
                *args,
                **kwargs
            )

        except GeminiQuotaExceeded:

            # ------------------------------------------------
            # DO NOT RETRY QUOTA ERRORS
            # ------------------------------------------------

            raise

        except Exception as error:

            last_error = error

            print(
                f"      Gemini attempt "
                f"{attempt}/{MAX_RETRIES} "
                f"failed: {error}"
            )

            # ------------------------------------------------
            # Do not retry permanent errors
            # ------------------------------------------------

            if not is_transient_error(
                error
            ):

                raise

            # ------------------------------------------------
            # Maximum retries reached
            # ------------------------------------------------

            if attempt >= MAX_RETRIES:

                break

            delay_index = min(
                attempt - 1,
                len(delays) - 1
            )

            delay = delays[
                delay_index
            ]

            print(
                f"      Retrying in "
                f"{delay:g} seconds..."
            )

            time.sleep(
                delay
            )

    raise last_error


# ============================================================
# GEMINI API
# ============================================================

def call_gemini(
    transactions
):
    """
    Send one batch to Gemini.
    """

    prompt = build_prompt(
        transactions
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    payload = {

        "contents": [

            {
                "parts": [

                    {
                        "text": prompt
                    }

                ]
            }

        ],

        "generationConfig": {

            "temperature": 0.1,

            "responseMimeType":
                "application/json"
        }
    }

    response = http_post_json(
        url,
        payload
    )

    try:

        candidates = response.get(
            "candidates",
            []
        )

        if not candidates:

            raise ValueError(
                "Gemini returned no "
                "candidates."
            )

        content = candidates[
            0
        ].get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        if not parts:

            raise ValueError(
                "Gemini returned no "
                "response parts."
            )

        text = parts[
            0
        ].get(
            "text",
            ""
        )

        results = extract_json_array(
            text
        )

        return validate_llm_results(
            results,
            transactions
        )

    except Exception as error:

        raise RuntimeError(
            f"Invalid Gemini response: "
            f"{error}"
        )


# ============================================================
# FALLBACK BATCH
# ============================================================

def fallback_batch(
    batch
):
    """
    Run deterministic investigation on a batch.
    """

    results = []

    for transaction in batch:

        results.append(
            deterministic_investigation(
                transaction
            )
        )

    return results


# ============================================================
# PROCESS ONE BATCH
# ============================================================

def process_batch(batch, batch_number, total_batches):
    print(f"\nBatch {batch_number}/{total_batches} ({len(batch)} exceptions)")

    if not GEMINI_API_KEY:
        print("  ⚠ GEMINI_API_KEY not configured.")
        print("  → Gemini disabled.")
        print("  → Using deterministic fallback.")
        return fallback_batch(batch), False

    try:
        results = call_with_retry(call_gemini, batch)
        print(f"  ✓ Gemini successfully investigated {len(results)} exceptions")
        return results, True

    except GeminiQuotaExceeded as error:
        print("\n  ⚠ GEMINI QUOTA EXHAUSTED")
        print(f"  {error}")
        print("  → Gemini calls will be disabled for the remaining batches.")
        print("  → Using deterministic fallback.")
        return fallback_batch(batch), False

    except Exception as error:
        print(f"  ✗ Gemini failed: {error}")
        print("  → Using deterministic fallback for this batch.")
        return fallback_batch(batch), True
# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results
):
    """
    Save final investigation results.
    """

    output_directory = os.path.dirname(
        OUTPUT_FILE
    )

    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    results
):
    """
    Print investigation summary.
    """

    total = len(
        results
    )

    gemini_count = sum(
        1
        for result in results
        if result.get(
            "source"
        ) == "gemini"
    )

    fallback_count = sum(
        1
        for result in results
        if result.get(
            "source"
        ) == "deterministic_fallback"
    )

    high_risk = sum(
        1
        for result in results
        if normalize_text(
            result.get("risk")
        ) == "HIGH"
    )

    medium_risk = sum(
        1
        for result in results
        if normalize_text(
            result.get("risk")
        ) == "MEDIUM"
    )

    low_risk = sum(
        1
        for result in results
        if normalize_text(
            result.get("risk")
        ) == "LOW"
    )

    human_review = sum(
        1
        for result in results
        if result.get(
            "needs_human_review"
        ) is True
    )

    print("\n")

    print("=" * 60)

    print(
        "LEDGERPILOT AI INVESTIGATION COMPLETE"
    )

    print("=" * 60)

    print(
        f"Total exceptions investigated : "
        f"{total}"
    )

    print(
        f"Gemini investigations          : "
        f"{gemini_count}"
    )

    print(
        f"Deterministic fallbacks        : "
        f"{fallback_count}"
    )

    print(
        f"High risk                      : "
        f"{high_risk}"
    )

    print(
        f"Medium risk                    : "
        f"{medium_risk}"
    )

    print(
        f"Low risk                       : "
        f"{low_risk}"
    )

    print(
        f"Human review required          : "
        f"{human_review}"
    )

    print(
        f"\nOutput saved to: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "LEDGERPILOT AI INVESTIGATOR"
    )

    print("=" * 60)

    print(
        f"Gemini model : "
        f"{GEMINI_MODEL}"
    )

    print(
        f"Batch size   : "
        f"{BATCH_SIZE}"
    )

    print(
        f"Timeout      : "
        f"{LLM_TIMEOUT_SECONDS}s"
    )

    print(
        f"Max retries  : "
        f"{MAX_RETRIES}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Load exceptions
    # --------------------------------------------------------

    transactions = load_transactions()

    print(
        f"\nExceptions to investigate: "
        f"{len(transactions)}"
    )

    if not transactions:

        print(
            "\nNo exceptions found."
        )

        print(
            "Check that "
            "diagnosed_transactions.csv "
            "contains exception rows."
        )

        return

    # --------------------------------------------------------
    # Create batches
    # --------------------------------------------------------

    batches = [

        transactions[
            i:i + BATCH_SIZE
        ]

        for i in range(
            0,
            len(transactions),
            BATCH_SIZE
        )
    ]

    total_batches = len(
        batches
    )

    print(
        f"Processing "
        f"{total_batches} Gemini batches..."
    )

    # --------------------------------------------------------
    # Process batches
    # --------------------------------------------------------

    all_results = []

    # Gemini is initially available.

    gemini_available = True

    for index, batch in enumerate(
        batches,
        start=1
    ):

        # ----------------------------------------------------
        # If quota was already exhausted,
        # don't call Gemini again.
        # ----------------------------------------------------

        if not gemini_available:

            print(
                f"\nBatch {index}/"
                f"{total_batches} "
                f"({len(batch)} exceptions)"
            )

            print(
                "  → Gemini disabled "
                "because quota was exhausted."
            )

            print(
                "  → Using deterministic "
                "fallback."
            )

            results = fallback_batch(
                batch
            )

        else:

            results, gemini_available = (
                process_batch(
                    batch,
                    index,
                    total_batches
                )
            )

        all_results.extend(
            results
        )

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    if len(all_results) != len(
        transactions
    ):

        raise RuntimeError(
            f"Investigation count mismatch. "
            f"Expected "
            f"{len(transactions)}, "
            f"got "
            f"{len(all_results)}."
        )

    # --------------------------------------------------------
    # Check duplicate IDs
    # --------------------------------------------------------

    result_ids = [
        result.get(
            "transaction_id"
        )
        for result in all_results
    ]

    if len(
        set(result_ids)
    ) != len(result_ids):

        raise RuntimeError(
            "Final output contains "
            "duplicate transaction IDs."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_results(
        all_results
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print_summary(
        all_results
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()