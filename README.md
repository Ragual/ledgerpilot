# LedgerPilot

### AI-Assisted Finance Reconciliation & Exception Management

LedgerPilot is a finance-operations prototype that automates transaction reconciliation, identifies settlement exceptions, generates evidence-backed investigations, applies independent safety guardrails, prioritizes high-risk cases, and routes sensitive cases for human review.

The system is designed around a simple principle:

> **AI recommends. Guardrails decide. Humans remain in control of financial decisions.**

---

## 🚀 Overview

Finance teams often need to reconcile payment records against bank settlements and investigate exceptions such as:

* Missing settlements
* Partial settlements
* Processing-fee mismatches
* Duplicate settlements
* Unexpected settlements

LedgerPilot turns this workflow into an end-to-end pipeline:

```text
Payment Data
     │
     ▼
Reconciliation Engine
     │
     ▼
Exception Detection
     │
     ▼
Evidence Engine
     │
     ▼
AI Investigation
     │
     ▼
Independent Guardrails
     │
     ▼
Priority Engine
     │
     ▼
Human Review
     │
     ▼
Finance Dashboard
```

---

## ✨ Key Features

### 1. Transaction Reconciliation

Compares payment records against bank settlement records and classifies transactions into:

```text
MATCHED
FAILED_PAYMENT
AMOUNT_MISMATCH
PARTIAL_SETTLEMENT
MISSING_SETTLEMENT
DUPLICATE_SETTLEMENT
UNEXPECTED_SETTLEMENT
```

### 2. Evidence-Based Investigation

Every detected exception is accompanied by supporting evidence such as:

* Payment amount
* Bank settlement amount
* Financial difference
* Settlement availability
* Duplicate-record detection
* Partial-settlement percentage

This makes system decisions explainable rather than opaque.

### 3. AI Investigation Layer

LedgerPilot includes an LLM investigation layer designed to return structured results:

```json
{
  "transaction_id": "TX0001",
  "diagnosis": "Missing settlement",
  "reason": "No corresponding bank settlement was found.",
  "confidence": 0.95,
  "recommended_action": "Investigate settlement status",
  "risk": "HIGH",
  "needs_human_review": true
}
```

The AI layer is separated from the deterministic finance logic so the application can continue operating safely when the external model is unavailable.

### 4. Safe AI Fallback

When the Gemini API quota is unavailable, LedgerPilot falls back to deterministic investigation rules.

This ensures the application does not stop functioning because of external AI availability.

The system explicitly records whether an investigation came from:

```text
gemini
```

or:

```text
fallback
```

### 5. Independent Guardrails

The AI output is not trusted blindly.

A separate guardrail layer evaluates:

* Risk
* Confidence
* Exception type
* Financial discrepancy
* Restricted financial actions

Example:

```text
AI Recommendation
       ↓
Guardrail Engine
       ↓
AUTO_REVIEW
HUMAN_REVIEW
BLOCK
```

The system does not directly authorize payments, refunds, transfers, or other financial transactions.

### 6. Exception Prioritization

Each exception receives a 0–100 priority score based on:

```text
Financial exposure
+
Exception severity
+
Risk
+
AI uncertainty
```

Priority levels:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

### 7. Human Review Workflow

High-risk cases can be reviewed through the dashboard.

Reviewers can record:

```text
APPROVE_RECONCILIATION
REJECT_RECOMMENDATION
ESCALATE
```

Reviewer decisions are stored in:

```text
data/review_log.json
```

The approval workflow is intentionally limited to reconciliation decisions and does not execute money movement.

### 8. Interactive Dashboard

The Streamlit dashboard provides:

* Transaction KPIs
* Match rate
* Exception exposure
* Actual discrepancy
* Exception breakdown
* Priority distribution
* Top-priority exceptions
* AI investigations
* Guardrail decisions
* Transaction-level investigation
* Human review
* Evaluation results

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │    Payment Data      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Reconciliation Engine│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Exception Detection │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Evidence Engine   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   AI Investigator    │
                         │ Gemini / Fallback    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Guardrail Engine    │
                         └──────┬─────┬─────┬───┘
                                │     │     │
                                ▼     ▼     ▼
                              AUTO  HUMAN  BLOCK
                              REVIEW REVIEW
                                │
                                └───────┐
                                        ▼
                              ┌──────────────────────┐
                              │    Priority Engine   │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │   Streamlit Dashboard │
                              └──────────────────────┘
```

---

# 📁 Project Structure

```text
ledgerpilot/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── app.py
├── app_dashboard.py
├── bank_generator.py
├── README.md
│
├── data/
│   ├── payments.csv
│   ├── bank_statement.csv
│   ├── ground_truth.csv
│   ├── reconciliation.csv
│   ├── diagnosed_transactions.csv
│   ├── evidence_results.json
│   ├── real_ai_investigations.json
│   ├── guardrail_results.json
│   ├── priority_results.json
│   ├── review_log.json
│   └── adversarial_cases.csv
│
├── database/
│
├── models/
│
└── services/
    ├── reconcile.py
    ├── diagnose.py
    ├── evidence.py
    ├── ai_investigator.py
    ├── guardrails.py
    ├── priority.py
    ├── evaluate.py
    ├── evaluate_model.py
    ├── adversarial_tests.py
    ├── evaluate_adversarial.py
    └── stress_test.py
```

---

# 🛠️ Technology Stack

| Layer                  | Technology                 |
| ---------------------- | -------------------------- |
| Language               | Python                     |
| Data Processing        | Python CSV / Pandas        |
| Dashboard              | Streamlit                  |
| AI Integration         | Google Gemini API          |
| AI Fallback            | Deterministic Python rules |
| Evaluation             | Python                     |
| Data Format            | CSV / JSON                 |
| Environment Management | `.env` / `python-dotenv`   |
| Version Control        | Git / GitHub               |

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd ledgerpilot
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure the API key

Copy the example environment file:

copy .env.example .env

Then open .env and add your Gemini API key:

GEMINI_API_KEY=YOUR_API_KEY
GEMINI_MODEL=gemini-3.6-flash

Never commit your .env file.

If a Gemini API key is not configured, LedgerPilot automatically uses its deterministic fallback investigation engine.

# ▶️ Running LedgerPilot

## Generate payment data

```bash
python app.py
```

## Generate bank statement + independent ground truth

```bash
python bank_generator.py
```

## Run reconciliation

```bash
python services/reconcile.py
```

## Generate diagnoses

```bash
python services/diagnose.py
```

## Generate evidence

```bash
python services/evidence.py
```

## Run evaluation

```bash
python services/evaluate.py
```

## Run AI investigation

```bash
python services/ai_investigator.py
```

If the Gemini quota is unavailable, the system automatically falls back to deterministic investigation logic.

## Run guardrails

```bash
python services/guardrails.py
```

## Run priority analysis

```bash
python services/priority.py
```

## Run adversarial tests

```bash
python services/adversarial_tests.py
python services/evaluate_adversarial.py
```

## Run stress tests

```bash
python services/stress_test.py
```

## Launch dashboard

```bash
python -m streamlit run app_dashboard.py
```

---

# 📊 Current Synthetic Benchmark

The current controlled benchmark contains:

```text
500 transactions
```

Current reconciliation distribution:

```text
MATCHED:               274
FAILED_PAYMENT:        115
AMOUNT_MISMATCH:        39
PARTIAL_SETTLEMENT:     44
MISSING_SETTLEMENT:     22
DUPLICATE_SETTLEMENT:    6
```

This results in:

```text
111 detected exceptions
```

Current financial measurements:

```text
Automatic match rate:      54.80%
Exception exposure:        ₹318,189.00
Actual discrepancy:        ₹82,881.75
```

### Exception breakdown

```text
AMOUNT_MISMATCH:       39
PARTIAL_SETTLEMENT:    44
MISSING_SETTLEMENT:    22
DUPLICATE_SETTLEMENT:   6
```

---

# 🧪 Validation & Testing

LedgerPilot includes multiple controlled test layers.

## Independent Synthetic Benchmark

The system compares:

```text
ground_truth.csv
        vs
reconciliation.csv
```

The current controlled dataset produced:

```text
500 / 500 exact scenario matches
```

Binary exception detection:

```text
Accuracy:  100%
Precision: 100%
Recall:    100%
F1 Score:  100%
```

### Important interpretation

These results are from a controlled synthetic dataset whose scenarios are generated specifically for this prototype.

They should **not** be interpreted as production or real-world accuracy.

---

## Manual Adversarial Tests

LedgerPilot includes deliberately constructed edge cases covering:

* Amount mismatches
* Partial settlements
* Missing settlements
* Duplicate settlements
* Normal matches

Current result:

```text
8 tests
8 passed
0 failed
```

---

## Randomized Stress Tests

The project also generates randomized synthetic edge cases.

Current run:

```text
100 tests
100 passed
0 failed
```

These tests are useful for regression testing and validating the classification logic across different transaction amounts and scenarios.

---

# 🛡️ Safety Design

LedgerPilot follows a human-in-the-loop approach.

The system separates:

```text
AI recommendation
```

from:

```text
financial authorization
```

The AI cannot directly execute:

```text
Payments
Refunds
Transfers
Withdrawals
```

High-risk or uncertain cases are routed for human review.

The guardrail system can also block restricted recommendations.

This separation is intentional because finance workflows require stronger controls than a generic AI assistant.

---

# 🤖 AI Design

The AI layer is designed to operate on structured transaction evidence rather than unrestricted business data.

Input:

```text
Transaction ID
Payment amount
Bank amount
Difference
Exception type
Existing evidence
```

Output:

```text
Diagnosis
Reason
Confidence
Recommended action
Risk
Human-review requirement
```

The response is validated before the application accepts it.

Validation includes:

* Required fields
* Confidence range
* Risk values
* Structured JSON parsing

---

# 🔁 Resilient AI Architecture

LedgerPilot does not depend completely on an external LLM.

```text
                    ┌───────────────┐
                    │ AI Request    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Gemini API    │
                    └───────┬───────┘
                            │
                       Available?
                       /        \
                     Yes         No
                      │           │
                      ▼           ▼
                   Gemini      Deterministic
                   Result        Fallback
                      \           /
                       \         /
                        ▼       ▼
                         Decision
                            │
                            ▼
                        Guardrails
                            │
                            ▼
                       Human Review
```

---

# 🎯 Example Investigation

Example missing settlement:

```text
Transaction: TX0143

Payment: ₹9,999.00
Bank: ₹0.00

Exception:
MISSING_SETTLEMENT

Diagnosis:
Successful payment has no matching bank settlement.

Risk:
HIGH

Priority:
CRITICAL

Recommended action:
Investigate settlement status and payout records.

Guardrail:
HUMAN_REVIEW
```

Example small fee mismatch:

```text
Payment: ₹999.00
Bank: ₹949.00

Difference:
₹50.00

Diagnosis:
Possible processing fee or settlement adjustment.

Risk:
LOW

Guardrail:
AUTO_REVIEW
```

`AUTO_REVIEW` means the case passed the current risk controls for automated review/reconciliation handling. It does **not** mean money is automatically transferred or refunded.

---

# 📈 Priority Scoring

Priority is calculated using a weighted scoring model:

```text
Financial Exposure       0–40
Exception Severity       0–30
Risk                     0–20
AI Uncertainty           0–10
                       --------
Total                    0–100
```

Priority bands:

```text
80–100  → CRITICAL
60–79   → HIGH
35–59   → MEDIUM
0–34    → LOW
```

The goal is to help finance teams focus on the most important cases first rather than treating every exception equally.

---

# 👤 Human Review

The dashboard provides a review workflow for cases that require human intervention.

Reviewers can:

```text
APPROVE_RECONCILIATION
REJECT_RECOMMENDATION
ESCALATE
```

Each decision is logged with:

```text
Transaction ID
Decision
Reviewer note
Timestamp
```

Stored in:

```text
data/review_log.json
```

The workflow is intentionally non-executing with respect to money movement.

---

# 📋 Evaluation Philosophy

LedgerPilot separates three different concepts:

### Exception exposure

The total payment value associated with exception cases.

### Actual discrepancy

The observed difference between payment and bank amounts for applicable mismatch/partial-settlement cases.

### Priority

A risk-oriented ranking indicating which exception should receive attention first.

These measurements should not be conflated with actual financial loss.

---

# ⚠️ Limitations

LedgerPilot is currently a prototype using synthetic financial data.

Important limitations include:

1. The dataset is simulated and does not represent real payment-provider traffic.

2. The current Gemini integration may fall back to deterministic reasoning when API quota or availability is limited.

3. Current evaluation results measure performance on controlled synthetic scenarios, not production transactions.

4. The project does not currently execute real payment, refund, transfer, or settlement operations.

5. A production deployment would require stronger authentication, authorization, observability, data encryption, audit controls, secret management, database persistence, and compliance/security review.

---

# 🔮 Future Improvements

Potential next steps include:

* PostgreSQL-backed transaction storage
* Real Razorpay webhook integration
* Settlement batch ingestion
* Merchant-level reconciliation
* Historical anomaly detection
* Learned exception classification
* Better fee-policy modeling
* Multi-provider payment reconciliation
* Approval workflows with authenticated users
* Role-based access control
* Production audit logs
* Notifications for critical exceptions
* Observability and monitoring
* Larger evaluation datasets
* Human-feedback loops for model improvement

---

# 🎥 Demo Flow

A recommended Buildathon demo flow:

```text
1. Open LedgerPilot dashboard

2. Show:
   500 transactions
   274 matched
   111 exceptions

3. Open Top Priority Exceptions

4. Select a CRITICAL missing settlement

5. Show:
   Payment amount
   Bank amount
   Difference
   Diagnosis
   Confidence
   Risk

6. Show Guardrail Decision

7. Show Priority Score

8. Open Human Review

9. Record a reviewer decision

10. Show the audit log
```

The core story:

> **LedgerPilot detects the exception, explains why it exists, assesses its risk, prevents unsafe automation, and routes the case to the right human.**

---

# 🏆 Why LedgerPilot

LedgerPilot is not simply an LLM wrapper.

Its architecture combines:

```text
Deterministic reconciliation
+
Evidence generation
+
AI investigation
+
Independent guardrails
+
Priority scoring
+
Human review
+
Audit logging
```

The goal is to combine the strengths of deterministic financial logic and AI reasoning while keeping financial decisions controllable and explainable.

---

# 📄 License

## License

This project is licensed under the [MIT License](LICENSE).

---

# 👨‍💻 Author

**Ragual**

Built as a finance-operations AI prototype for a payment/fintech Buildathon.

---

## ⭐ Project Summary

**LedgerPilot** is an AI-assisted finance reconciliation platform that detects settlement exceptions, explains them using structured evidence, prioritizes financial risk, applies independent guardrails, and keeps humans in control of sensitive decisions.
