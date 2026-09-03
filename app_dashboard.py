import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="LedgerPilot",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# HELPERS
# =========================================================

def load_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()

    return pd.read_csv(path)


def load_json(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_review_decision(transaction_id, decision, reviewer_note):
    path = "data/review_log.json"

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            reviews = json.load(file)
    else:
        reviews = []

    review = {
        "transaction_id": transaction_id,
        "decision": decision,
        "reviewer_note": reviewer_note,
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }

    reviews.append(review)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(reviews, file, indent=4)

    return review


# =========================================================
# LOAD DATA
# =========================================================

payments = load_csv("data/payments.csv")
reconciliation = load_csv("data/reconciliation.csv")
diagnosed = load_csv("data/diagnosed_transactions.csv")

ai_results = load_json(
    "data/real_ai_investigations.json"
)

guardrail_results = load_json(
    "data/guardrail_results.json"
)

priority_results = load_json(
    "data/priority_results.json"
)


priority_df = pd.DataFrame(priority_results)
guardrail_df = pd.DataFrame(guardrail_results)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💳 LedgerPilot")

st.sidebar.caption(
    "AI Finance Operations"
)

st.sidebar.divider()

st.sidebar.markdown(
    """
### Pipeline

✅ Transaction ingestion  
✅ Reconciliation  
✅ Exception detection  
✅ Evidence analysis  
✅ AI investigation  
✅ Guardrails  
✅ Priority ranking
"""
)

st.sidebar.divider()

st.sidebar.caption(
    "Synthetic dataset • 500 transactions"
)


# =========================================================
# VALIDATION
# =========================================================

if payments.empty or reconciliation.empty:

    st.error(
        "Required data files are missing."
    )

    st.stop()


# =========================================================
# CORE METRICS
# =========================================================

total_transactions = len(payments)

matched = len(
    reconciliation[
        reconciliation["result"] == "MATCHED"
    ]
)

failed = len(
    reconciliation[
        reconciliation["result"] == "FAILED_PAYMENT"
    ]
)

amount_mismatch = len(
    reconciliation[
        reconciliation["result"] == "AMOUNT_MISMATCH"
    ]
)

partial_settlement = len(
    reconciliation[
        reconciliation["result"] == "PARTIAL_SETTLEMENT"
    ]
)

missing_settlement = len(
    reconciliation[
        reconciliation["result"] == "MISSING_SETTLEMENT"
    ]
)

duplicate_settlement = len(
    reconciliation[
        reconciliation["result"] == "DUPLICATE_SETTLEMENT"
    ]
)

exceptions = (
    amount_mismatch
    + partial_settlement
    + missing_settlement
    + duplicate_settlement
)

match_rate = (
    matched / total_transactions * 100
    if total_transactions
    else 0
)


# =========================================================
# FINANCIAL METRICS
# =========================================================

exception_exposure = 0.0
actual_discrepancy = 0.0


for _, row in reconciliation.iterrows():

    result = row["result"]

    payment_amount = float(
        row["payment_amount"]
    )

    bank_amount = float(
        row["bank_amount"]
    )

    difference = abs(
        payment_amount - bank_amount
    )


    if result in [
        "AMOUNT_MISMATCH",
        "PARTIAL_SETTLEMENT",
        "MISSING_SETTLEMENT",
        "DUPLICATE_SETTLEMENT"
    ]:

        exception_exposure += payment_amount


    if result in [
        "AMOUNT_MISMATCH",
        "PARTIAL_SETTLEMENT"
    ]:

        actual_discrepancy += difference


# =========================================================
# GUARDRAIL METRICS
# =========================================================

auto_review = 0
human_review = 0
blocked = 0


if not guardrail_df.empty:

    auto_review = len(
        guardrail_df[
            guardrail_df["decision"]
            == "AUTO_REVIEW"
        ]
    )

    human_review = len(
        guardrail_df[
            guardrail_df["decision"]
            == "HUMAN_REVIEW"
        ]
    )

    blocked = len(
        guardrail_df[
            guardrail_df["decision"]
            == "BLOCK"
        ]
    )


# =========================================================
# PRIORITY METRICS
# =========================================================

critical = 0
high = 0
medium = 0
low = 0

critical_exposure = 0.0


if not priority_df.empty:

    critical = len(
        priority_df[
            priority_df["priority"]
            == "CRITICAL"
        ]
    )

    high = len(
        priority_df[
            priority_df["priority"]
            == "HIGH"
        ]
    )

    medium = len(
        priority_df[
            priority_df["priority"]
            == "MEDIUM"
        ]
    )

    low = len(
        priority_df[
            priority_df["priority"]
            == "LOW"
        ]
    )

    critical_exposure = priority_df.loc[
        priority_df["priority"] == "CRITICAL",
        "payment_amount"
    ].sum()


# =========================================================
# HEADER
# =========================================================

st.title("💳 LedgerPilot")

st.markdown(
    "## AI Finance Reconciliation & Exception Management"
)

st.caption(
    "Evidence-driven reconciliation with AI investigation, "
    "independent guardrails and financial exception prioritization."
)


# =========================================================
# KPI ROW 1
# =========================================================

st.markdown("### System Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Transactions",
        f"{total_transactions:,}"
    )

with col2:

    st.metric(
        "Matched",
        f"{matched:,}"
    )

with col3:

    st.metric(
        "Match Rate",
        f"{match_rate:.1f}%"
    )

with col4:

    st.metric(
        "Actual Discrepancy",
        f"₹{actual_discrepancy:,.0f}"
    )


# =========================================================
# KPI ROW 2
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Exceptions",
        f"{exceptions:,}"
    )

with col2:

    st.metric(
        "Exception Exposure",
        f"₹{exception_exposure:,.0f}"
    )

with col3:

    st.metric(
        "Human Review",
        f"{human_review:,}"
    )

with col4:

    st.metric(
        "Blocked",
        f"{blocked:,}"
    )


st.divider()


# =========================================================
# PRIORITY OVERVIEW
# =========================================================

st.markdown("## 🎯 Priority Overview")

priority_summary = pd.DataFrame(
    {
        "Priority": [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW"
        ],
        "Cases": [
            critical,
            high,
            medium,
            low
        ]
    }
)

col1, col2 = st.columns(2)

with col1:

    st.markdown(
        "#### Exception Priority Distribution"
    )

    st.bar_chart(
        priority_summary.set_index(
            "Priority"
        )
    )


with col2:

    st.markdown(
        "#### Priority Metrics"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Critical Cases",
            critical
        )

    with c2:

        st.metric(
            "Critical Exposure",
            f"₹{critical_exposure:,.0f}"
        )

    st.caption(
        "Critical exposure represents the payment "
        "value associated with CRITICAL exceptions."
    )


st.divider()


# =========================================================
# RECONCILIATION STATUS
# =========================================================

st.markdown("## 📊 Reconciliation Overview")

status_data = pd.DataFrame(
    {
        "Status": [
            "Matched",
            "Amount Mismatch",
            "Partial Settlement",
            "Missing Settlement",
            "Duplicate Settlement",
            "Failed Payment"
        ],
        "Count": [
            matched,
            amount_mismatch,
            partial_settlement,
            missing_settlement,
            duplicate_settlement,
            failed
        ]
    }
)

col1, col2 = st.columns(2)

with col1:

    st.markdown("#### Transaction Status")

    st.bar_chart(
        status_data.set_index(
            "Status"
        )
    )


with col2:

    st.markdown("#### Guardrail Decisions")

    if not guardrail_df.empty:

        decision_counts = (
            guardrail_df["decision"]
            .value_counts()
        )

        st.bar_chart(
            decision_counts
        )

    else:

        st.info(
            "No guardrail results available."
        )


st.divider()


# =========================================================
# TOP PRIORITY CASES
# =========================================================

st.markdown("## 🚨 Top Priority Exceptions")

if not priority_df.empty:

    top_priority = priority_df[
        [
            "transaction_id",
            "exception_type",
            "payment_amount",
            "difference",
            "risk",
            "priority_score",
            "priority"
        ]
    ].head(15).copy()

    top_priority.rename(
        columns={
            "transaction_id":
                "Transaction",

            "exception_type":
                "Exception",

            "payment_amount":
                "Payment (₹)",

            "difference":
                "Exposure / Difference (₹)",

            "risk":
                "Risk",

            "priority_score":
                "Score",

            "priority":
                "Priority"
        },
        inplace=True
    )

    st.dataframe(
        top_priority,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Priority results are unavailable."
    )


st.divider()


# =========================================================
# AI INVESTIGATION
# =========================================================

st.markdown("## 🤖 AI Investigation")

if ai_results:

    ai_df = pd.DataFrame(
        ai_results
    )

    ai_columns = [
        "transaction_id",
        "diagnosis",
        "confidence",
        "risk",
        "needs_human_review",
        "source"
    ]

    available = [
        column
        for column in ai_columns
        if column in ai_df.columns
    ]

    ai_display = ai_df[
        available
    ].copy()

    if "confidence" in ai_display.columns:

        ai_display["confidence"] = (
            ai_display["confidence"] * 100
        ).round(1)

        ai_display.rename(
            columns={
                "confidence":
                    "Confidence (%)"
            },
            inplace=True
        )

    ai_display.rename(
        columns={
            "transaction_id":
                "Transaction",

            "diagnosis":
                "Diagnosis",

            "risk":
                "Risk",

            "needs_human_review":
                "Human Review",

            "source":
                "Source"
        },
        inplace=True
    )

    st.dataframe(
        ai_display,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No AI investigation results available."
    )


st.divider()


# =========================================================
# TRANSACTION INVESTIGATION
# =========================================================

st.markdown("## 🔎 Transaction Investigation")

exception_ids = priority_df[
    "transaction_id"
].tolist() if not priority_df.empty else []


if exception_ids:

    selected_transaction = st.selectbox(
        "Select a transaction",
        exception_ids
    )


    # ---------------------------------------------
    # Reconciliation data
    # ---------------------------------------------

    selected_rows = reconciliation[
        reconciliation["transaction_id"]
        == selected_transaction
    ]


    if not selected_rows.empty:

        selected = selected_rows.iloc[0]

        payment_amount = float(
            selected["payment_amount"]
        )

        bank_amount = float(
            selected["bank_amount"]
        )

        difference = (
            payment_amount
            - bank_amount
        )


        st.markdown(
            f"### {selected_transaction}"
        )


        c1, c2, c3 = st.columns(3)


        with c1:

            st.metric(
                "Payment",
                f"₹{payment_amount:,.2f}"
            )


        with c2:

            st.metric(
                "Bank Settlement",
                f"₹{bank_amount:,.2f}"
            )


        with c3:

            st.metric(
                "Difference",
                f"₹{difference:,.2f}"
            )


        # ---------------------------------------------
        # AI details
        # ---------------------------------------------

        selected_ai = None

        for result in ai_results:

            if (
                result.get(
                    "transaction_id"
                )
                == selected_transaction
            ):

                selected_ai = result

                break


        if selected_ai:

            st.markdown(
                "### 🤖 AI Analysis"
            )

            c1, c2 = st.columns(2)


            with c1:

                st.write(
                    f"**Diagnosis:** "
                    f"{selected_ai.get(
                        'diagnosis',
                        'N/A'
                    )}"
                )

                st.write(
                    f"**Reason:** "
                    f"{selected_ai.get(
                        'reason',
                        'N/A'
                    )}"
                )


            with c2:

                confidence = float(
                    selected_ai.get(
                        "confidence",
                        0
                    )
                )

                st.write(
                    f"**Confidence:** "
                    f"{confidence * 100:.1f}%"
                )

                st.write(
                    f"**Risk:** "
                    f"{selected_ai.get(
                        'risk',
                        'N/A'
                    )}"
                )

                st.write(
                    f"**Human Review:** "
                    f"{selected_ai.get(
                        'needs_human_review',
                        'N/A'
                    )}"
                )


        # ---------------------------------------------
        # Guardrail details
        # ---------------------------------------------

        selected_guardrail = None

        for result in guardrail_results:

            if (
                result.get(
                    "transaction_id"
                )
                == selected_transaction
            ):

                selected_guardrail = result

                break


        if selected_guardrail:

            st.markdown(
                "### 🛡️ Guardrail Decision"
            )

            c1, c2, c3 = st.columns(3)


            with c1:

                st.write(
                    f"**Decision:** "
                    f"{selected_guardrail.get(
                        'decision',
                        'N/A'
                    )}"
                )


            with c2:

                st.write(
                    f"**Allowed Action:** "
                    f"{selected_guardrail.get(
                        'allowed_action',
                        'N/A'
                    )}"
                )


            with c3:

                st.write(
                    f"**Risk:** "
                    f"{selected_guardrail.get(
                        'risk',
                        'N/A'
                    )}"
                )


            reasons = selected_guardrail.get(
                "guardrail_reasons",
                []
            )


            if reasons:

                st.write(
                    "**Guardrail Reasons:**"
                )

                for reason in reasons:

                    st.write(
                        f"✓ {reason}"
                    )


        # ---------------------------------------------
        # Priority details
        # ---------------------------------------------

        if not priority_df.empty:

            priority_rows = priority_df[
                priority_df["transaction_id"]
                == selected_transaction
            ]


            if not priority_rows.empty:

                selected_priority = (
                    priority_rows.iloc[0]
                )


                st.markdown(
                    "### 🎯 Priority Assessment"
                )

                c1, c2, c3 = st.columns(3)


                with c1:

                    st.metric(
                        "Priority Score",
                        f"{int(selected_priority['priority_score'])}/100"
                    )


                with c2:

                    st.metric(
                        "Priority",
                        selected_priority["priority"]
                    )


                with c3:

                    st.metric(
                        "Risk",
                        selected_priority["risk"]
                    )


else:

    st.success(
        "No exceptions available."
    )


st.divider()

# =========================================================
# HUMAN REVIEW WORKFLOW
# =========================================================

st.divider()

st.markdown("## 👤 Human Review")

st.caption(
    "Review AI recommendations before reconciliation. "
    "No payment, refund, transfer, or other financial action "
    "is executed by this workflow."
)


review_candidates = []

if not priority_df.empty:

    review_candidates = priority_df[
        priority_df["transaction_id"].isin(
            guardrail_df.loc[
                guardrail_df["decision"] == "HUMAN_REVIEW",
                "transaction_id"
            ].tolist()
            if not guardrail_df.empty
            and "decision" in guardrail_df.columns
            else []
        )
    ]["transaction_id"].tolist()


if review_candidates:

    review_transaction = st.selectbox(
        "Select a case requiring human review",
        review_candidates,
        key="review_transaction"
    )

    review_rows = reconciliation[
        reconciliation["transaction_id"]
        == review_transaction
    ]

    if not review_rows.empty:

        review_case = review_rows.iloc[0]

        st.markdown(
            f"### Review Case: {review_transaction}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Payment",
                f"₹{float(review_case['payment_amount']):,.2f}"
            )

        with c2:
            st.metric(
                "Bank Amount",
                f"₹{float(review_case['bank_amount']):,.2f}"
            )

        with c3:
            st.metric(
                "Exception",
                review_case["result"]
            )

        # Find AI result
        review_ai = None

        for result in ai_results:

            if result.get(
                "transaction_id"
            ) == review_transaction:

                review_ai = result
                break

        if review_ai:

            st.markdown("#### AI Recommendation")

            st.write(
                f"**Diagnosis:** "
                f"{review_ai.get('diagnosis', 'N/A')}"
            )

            st.write(
                f"**Reason:** "
                f"{review_ai.get('reason', 'N/A')}"
            )

            st.write(
                f"**Recommended Action:** "
                f"{review_ai.get('recommended_action', 'N/A')}"
            )

            st.write(
                f"**Confidence:** "
                f"{float(review_ai.get('confidence', 0)) * 100:.1f}%"
            )

            st.write(
                f"**Risk:** "
                f"{review_ai.get('risk', 'N/A')}"
            )

        reviewer_note = st.text_area(
            "Reviewer note",
            placeholder=(
                "Explain why you approved, rejected, "
                "or escalated this recommendation."
            ),
            key="reviewer_note"
        )

        review_decision = st.radio(
            "Decision",
            [
                "APPROVE_RECONCILIATION",
                "REJECT_RECOMMENDATION",
                "ESCALATE"
            ],
            horizontal=True,
            key="review_decision"
        )

        if st.button(
            "Save Review Decision",
            type="primary"
        ):

            save_review_decision(
                review_transaction,
                review_decision,
                reviewer_note
            )

            st.success(
                f"Decision saved for {review_transaction}: "
                f"{review_decision}"
            )

            st.rerun()

else:

    st.success(
        "No cases currently require human review."
    )


# =========================================================
# REVIEW AUDIT LOG
# =========================================================

st.markdown("### 📋 Review Audit Log")

review_log_path = "data/review_log.json"

if os.path.exists(review_log_path):

    review_log = load_json(
        review_log_path
    )

    if review_log:

        review_log_df = pd.DataFrame(
            review_log
        )

        review_log_df.rename(
            columns={
                "transaction_id": "Transaction",
                "decision": "Decision",
                "reviewer_note": "Reviewer Note",
                "timestamp": "Timestamp"
            },
            inplace=True
        )

        st.dataframe(
            review_log_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No review decisions have been recorded yet."
        )

else:

    st.info(
        "No review decisions have been recorded yet."
    )

# =========================================================
# SYSTEM EVALUATION
# =========================================================

st.divider()

st.markdown("## 🧪 System Evaluation")

st.caption(
    "Controlled synthetic benchmarks used to validate "
    "LedgerPilot's reconciliation and exception handling."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Benchmark Records",
        "500"
    )

with col2:
    st.metric(
        "Adversarial Tests",
        "8 / 8"
    )

with col3:
    st.metric(
        "Random Stress Tests",
        "100 / 100"
    )

st.markdown("### Validation Results")

evaluation_data = pd.DataFrame(
    {
        "Test": [
            "500-record benchmark",
            "Manual adversarial suite",
            "Randomized stress suite"
        ],
        "Result": [
            "500 / 500",
            "8 / 8",
            "100 / 100"
        ],
        "Status": [
            "PASS",
            "PASS",
            "PASS"
        ]
    }
)

st.dataframe(
    evaluation_data,
    use_container_width=True,
    hide_index=True
)

st.info(
    "These results are controlled synthetic tests and "
    "should not be interpreted as production accuracy."
)

# =========================================================
# ARCHITECTURE
# =========================================================

st.markdown(
    "## 🧠 LedgerPilot Architecture"
)

st.code(
    """
                    LEDGERPILOT
                         │
                         ▼
                 Transaction Data
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
                  AI Investigator
                         │
                         ▼
                  Guardrail Engine
                    │     │     │
                    │     │     └── BLOCK
                    │     └──────── HUMAN REVIEW
                    └────────────── AUTO REVIEW
                         │
                         ▼
                  Priority Engine
                         │
                         ▼
                  Finance Dashboard
""",
    language="text"
)


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "LedgerPilot — AI-assisted finance operations "
    "with explainability, safety controls and prioritization."
)