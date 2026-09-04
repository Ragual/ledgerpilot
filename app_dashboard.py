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

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def load_json(path):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_review_decision(transaction_id, decision, reviewer_note):
    path = "data/review_log.json"

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                reviews = json.load(file)
        except Exception:
            reviews = []
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


def find_result(results, transaction_id):
    """
    Find a transaction result safely from a JSON result list.
    """
    for result in results:

        if str(result.get("transaction_id", "")).strip() == str(
            transaction_id
        ).strip():

            return result

    return None


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def format_confidence(value):
    """
    Supports either:
    0.95 -> 95.0%
    95 -> 95.0%
    """
    confidence = safe_float(value, 0.0)

    if confidence <= 1:
        confidence *= 100

    return f"{confidence:.1f}%"


# =========================================================
# LOAD DATA
# =========================================================

payments = load_csv(
    "data/payments.csv"
)

reconciliation = load_csv(
    "data/reconciliation.csv"
)

diagnosed = load_csv(
    "data/diagnosed_transactions.csv"
)

ai_results = load_json(
    "data/real_ai_investigations.json"
)

guardrail_results = load_json(
    "data/guardrail_results.json"
)

priority_results = load_json(
    "data/priority_results.json"
)


priority_df = pd.DataFrame(
    priority_results
)

guardrail_df = pd.DataFrame(
    guardrail_results
)


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

total_transactions = len(
    payments
)

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

    payment_amount = safe_float(
        row["payment_amount"]
    )

    bank_amount = safe_float(
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


if not guardrail_df.empty and "decision" in guardrail_df.columns:

    auto_review = len(
        guardrail_df[
            guardrail_df["decision"] == "AUTO_REVIEW"
        ]
    )

    human_review = len(
        guardrail_df[
            guardrail_df["decision"] == "HUMAN_REVIEW"
        ]
    )

    blocked = len(
        guardrail_df[
            guardrail_df["decision"] == "BLOCK"
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


if (
    not priority_df.empty
    and "priority" in priority_df.columns
):

    critical = len(
        priority_df[
            priority_df["priority"] == "CRITICAL"
        ]
    )

    high = len(
        priority_df[
            priority_df["priority"] == "HIGH"
        ]
    )

    medium = len(
        priority_df[
            priority_df["priority"] == "MEDIUM"
        ]
    )

    low = len(
        priority_df[
            priority_df["priority"] == "LOW"
        ]
    )

    if "payment_amount" in priority_df.columns:

        critical_exposure = pd.to_numeric(
            priority_df.loc[
                priority_df["priority"] == "CRITICAL",
                "payment_amount"
            ],
            errors="coerce"
        ).fillna(0).sum()


# =========================================================
# HEADER
# =========================================================

st.title(
    "💳 LedgerPilot"
)

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

st.markdown(
    "### System Overview"
)

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

st.markdown(
    "## 🎯 Priority Overview"
)

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

st.markdown(
    "## 📊 Reconciliation Overview"
)

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

    st.markdown(
        "#### Transaction Status"
    )

    st.bar_chart(
        status_data.set_index(
            "Status"
        )
    )


with col2:

    st.markdown(
        "#### Guardrail Decisions"
    )

    if not guardrail_df.empty and "decision" in guardrail_df.columns:

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

st.markdown(
    "## 🚨 Top Priority Exceptions"
)

if not priority_df.empty:

    available_priority_columns = [
        column
        for column in [
            "transaction_id",
            "exception_type",
            "payment_amount",
            "difference",
            "risk",
            "priority_score",
            "priority"
        ]
        if column in priority_df.columns
    ]

    top_priority = priority_df[
        available_priority_columns
    ].head(15).copy()

    top_priority.rename(
        columns={
            "transaction_id": "Transaction",
            "exception_type": "Exception",
            "payment_amount": "Payment (₹)",
            "difference": "Exposure / Difference (₹)",
            "risk": "Risk",
            "priority_score": "Score",
            "priority": "Priority"
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

st.markdown(
    "## 🤖 AI Investigation"
)

if ai_results:

    ai_df = pd.DataFrame(
        ai_results
    )

    ai_columns = [
        "transaction_id",
        "diagnosis",
        "reason",
        "recommended_action",
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
            pd.to_numeric(
                ai_display["confidence"],
                errors="coerce"
            )
            .fillna(0)
            * 100
        ).round(1)

        ai_display.rename(
            columns={
                "confidence": "Confidence (%)"
            },
            inplace=True
        )

    ai_display.rename(
        columns={
            "transaction_id": "Transaction",
            "diagnosis": "Diagnosis",
            "reason": "Reason",
            "recommended_action": "Recommended Action",
            "risk": "Risk",
            "needs_human_review": "Human Review",
            "source": "Source"
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

st.markdown(
    "## 🔎 Transaction Investigation"
)

# ---------------------------------------------------------
# Build exception transaction list
# ---------------------------------------------------------

if not priority_df.empty and "transaction_id" in priority_df.columns:

    exception_ids = (
        priority_df["transaction_id"]
        .astype(str)
        .tolist()
    )

else:

    exception_ids = (
        reconciliation[
            reconciliation["result"].isin(
                [
                    "AMOUNT_MISMATCH",
                    "PARTIAL_SETTLEMENT",
                    "MISSING_SETTLEMENT",
                    "DUPLICATE_SETTLEMENT"
                ]
            )
        ]["transaction_id"]
        .astype(str)
        .tolist()
    )


# Remove duplicates while preserving order

exception_ids = list(
    dict.fromkeys(exception_ids)
)


if exception_ids:

    selected_transaction = st.selectbox(
        "Select a transaction to investigate",
        exception_ids,
        key="transaction_investigation"
    )


    # =====================================================
    # RECONCILIATION DATA
    # =====================================================

    selected_rows = reconciliation[
        reconciliation["transaction_id"].astype(str)
        == str(selected_transaction)
    ]


    if not selected_rows.empty:

        selected = selected_rows.iloc[0]

        payment_amount = safe_float(
            selected["payment_amount"]
        )

        bank_amount = safe_float(
            selected["bank_amount"]
        )

        difference = (
            payment_amount
            - bank_amount
        )

        exception_type = str(
            selected.get(
                "result",
                "UNKNOWN"
            )
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


        st.caption(
            f"Exception Type: {exception_type}"
        )


        # =================================================
        # FIND AI RESULT
        # =================================================

        selected_ai = find_result(
            ai_results,
            selected_transaction
        )


        # =================================================
        # FIND DIAGNOSIS RESULT
        # =================================================

        selected_diagnosis = None

        if not diagnosed.empty and "transaction_id" in diagnosed.columns:

            diagnosis_rows = diagnosed[
                diagnosed["transaction_id"].astype(str)
                == str(selected_transaction)
            ]

            if not diagnosis_rows.empty:

                selected_diagnosis = (
                    diagnosis_rows.iloc[0]
                )


        # =================================================
        # AI ANALYSIS
        # =================================================

        st.markdown(
            "### 🤖 AI Analysis"
        )


        if selected_ai:

            # ---------------------------------------------
            # Diagnosis
            # ---------------------------------------------

            ai_diagnosis = selected_ai.get(
                "diagnosis"
            )

            if not ai_diagnosis or str(ai_diagnosis).lower() == "nan":

                if selected_diagnosis is not None:

                    ai_diagnosis = selected_diagnosis.get(
                        "diagnosis",
                        "N/A"
                    )

                else:

                    ai_diagnosis = "N/A"


            # ---------------------------------------------
            # Reason
            # ---------------------------------------------

            ai_reason = selected_ai.get(
                "reason"
            )

            if not ai_reason or str(ai_reason).lower() == "nan":

                if selected_diagnosis is not None:

                    ai_reason = (
                        selected_diagnosis.get(
                            "diagnosis",
                            "No additional reasoning available."
                        )
                    )

                else:

                    ai_reason = (
                        "No additional reasoning available."
                    )


            # ---------------------------------------------
            # Recommended Action
            # ---------------------------------------------

            ai_action = selected_ai.get(
                "recommended_action"
            )

            if not ai_action or str(ai_action).lower() == "nan":

                if selected_diagnosis is not None:

                    ai_action = selected_diagnosis.get(
                        "recommendation",
                        "Review the exception."
                    )

                else:

                    ai_action = "Review the exception."


            # ---------------------------------------------
            # Confidence
            # ---------------------------------------------

            ai_confidence = selected_ai.get(
                "confidence",
                0
            )


            # ---------------------------------------------
            # Risk
            # ---------------------------------------------

            ai_risk = selected_ai.get(
                "risk"
            )

            if not ai_risk or str(ai_risk).lower() == "nan":

                if selected_diagnosis is not None:

                    priority_value = str(
                        selected_diagnosis.get(
                            "priority",
                            "HIGH"
                        )
                    ).upper()

                    if priority_value == "LOW":
                        ai_risk = "LOW"

                    elif priority_value == "MEDIUM":
                        ai_risk = "MEDIUM"

                    else:
                        ai_risk = "HIGH"

                else:

                    ai_risk = "N/A"


            # ---------------------------------------------
            # Human Review
            # ---------------------------------------------

            needs_human_review = selected_ai.get(
                "needs_human_review"
            )

            if needs_human_review is None:

                needs_human_review = (
                    str(ai_risk).upper()
                    in ["HIGH", "MEDIUM"]
                )


            # ---------------------------------------------
            # Source
            # ---------------------------------------------

            ai_source = selected_ai.get(
                "source",
                "Unknown"
            )


            # ---------------------------------------------
            # Display
            # ---------------------------------------------

            c1, c2 = st.columns(2)


            with c1:

                st.write(
                    f"**Diagnosis:** {ai_diagnosis}"
                )

                st.write(
                    f"**Reason:** {ai_reason}"
                )

                st.write(
                    f"**Recommended Action:** {ai_action}"
                )


            with c2:

                st.write(
                    f"**Confidence:** "
                    f"{format_confidence(ai_confidence)}"
                )

                st.write(
                    f"**Risk:** {ai_risk}"
                )

                st.write(
                    f"**Human Review:** "
                    f"{'YES' if needs_human_review else 'NO'}"
                )

                st.write(
                    f"**AI Source:** {ai_source}"
                )


        else:

            # =================================================
            # FALLBACK IF AI RESULT IS MISSING
            # =================================================

            st.warning(
                "AI investigation record was not found for this transaction. "
                "Showing the deterministic diagnosis instead."
            )


            if selected_diagnosis is not None:

                diagnosis = selected_diagnosis.get(
                    "diagnosis",
                    "N/A"
                )

                recommendation = selected_diagnosis.get(
                    "recommendation",
                    "Review the exception."
                )

                confidence = selected_diagnosis.get(
                    "confidence",
                    0
                )

                priority_value = str(
                    selected_diagnosis.get(
                        "priority",
                        "HIGH"
                    )
                ).upper()


                if priority_value == "LOW":

                    fallback_risk = "LOW"
                    fallback_review = False

                elif priority_value == "MEDIUM":

                    fallback_risk = "MEDIUM"
                    fallback_review = True

                else:

                    fallback_risk = "HIGH"
                    fallback_review = True


                c1, c2 = st.columns(2)


                with c1:

                    st.write(
                        f"**Diagnosis:** {diagnosis}"
                    )

                    st.write(
                        f"**Reason:** {diagnosis}"
                    )

                    st.write(
                        f"**Recommended Action:** "
                        f"{recommendation}"
                    )


                with c2:

                    st.write(
                        f"**Confidence:** "
                        f"{format_confidence(confidence)}"
                    )

                    st.write(
                        f"**Risk:** {fallback_risk}"
                    )

                    st.write(
                        f"**Human Review:** "
                        f"{'YES' if fallback_review else 'NO'}"
                    )

                    st.write(
                        "**AI Source:** Deterministic Fallback"
                    )

            else:

                st.error(
                    "No investigation or diagnosis data "
                    "was found for this transaction."
                )


        # =================================================
        # GUARDRAIL DETAILS
        # =================================================

        selected_guardrail = find_result(
            guardrail_results,
            selected_transaction
        )


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

        else:

            st.info(
                "No guardrail result found for this transaction."
            )


        # =================================================
        # PRIORITY DETAILS
        # =================================================

        if not priority_df.empty:

            priority_rows = priority_df[
                priority_df["transaction_id"].astype(str)
                == str(selected_transaction)
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

                    priority_score = safe_float(
                        selected_priority.get(
                            "priority_score",
                            0
                        )
                    )

                    st.metric(
                        "Priority Score",
                        f"{int(priority_score)}/100"
                    )


                with c2:

                    st.metric(
                        "Priority",
                        str(
                            selected_priority.get(
                                "priority",
                                "N/A"
                            )
                        )
                    )


                with c3:

                    st.metric(
                        "Risk",
                        str(
                            selected_priority.get(
                                "risk",
                                "N/A"
                            )
                        )
                    )


    else:

        st.warning(
            "Reconciliation record not found for "
            f"{selected_transaction}."
        )


else:

    st.success(
        "No exceptions available."
    )


st.divider()


# =========================================================
# HUMAN REVIEW WORKFLOW
# =========================================================

st.markdown(
    "## 👤 Human Review"
)

st.caption(
    "Review AI recommendations before reconciliation. "
    "No payment, refund, transfer, or other financial action "
    "is executed by this workflow."
)


review_candidates = []


if (
    not priority_df.empty
    and "transaction_id" in priority_df.columns
):

    if (
        not guardrail_df.empty
        and "decision" in guardrail_df.columns
        and "transaction_id" in guardrail_df.columns
    ):

        human_review_ids = guardrail_df[
            guardrail_df["decision"] == "HUMAN_REVIEW"
        ]["transaction_id"].astype(str).tolist()


        review_candidates = priority_df[
            priority_df["transaction_id"].astype(str).isin(
                human_review_ids
            )
        ]["transaction_id"].astype(str).tolist()


if review_candidates:

    review_transaction = st.selectbox(
        "Select a case requiring human review",
        review_candidates,
        key="review_transaction"
    )


    review_rows = reconciliation[
        reconciliation["transaction_id"].astype(str)
        == str(review_transaction)
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
                f"₹{safe_float(review_case['payment_amount']):,.2f}"
            )


        with c2:

            st.metric(
                "Bank Amount",
                f"₹{safe_float(review_case['bank_amount']):,.2f}"
            )


        with c3:

            st.metric(
                "Exception",
                review_case["result"]
            )


        # =================================================
        # FIND AI RESULT
        # =================================================

        review_ai = find_result(
            ai_results,
            review_transaction
        )


        if review_ai:

            st.markdown(
                "#### 🤖 AI Recommendation"
            )


            diagnosis = review_ai.get(
                "diagnosis",
                "N/A"
            )

            reason = review_ai.get(
                "reason",
                "N/A"
            )

            recommended_action = review_ai.get(
                "recommended_action",
                "N/A"
            )

            confidence = review_ai.get(
                "confidence",
                0
            )

            risk = review_ai.get(
                "risk",
                "N/A"
            )


            st.write(
                f"**Diagnosis:** {diagnosis}"
            )

            st.write(
                f"**Reason:** {reason}"
            )

            st.write(
                f"**Recommended Action:** "
                f"{recommended_action}"
            )

            st.write(
                f"**Confidence:** "
                f"{format_confidence(confidence)}"
            )

            st.write(
                f"**Risk:** {risk}"
            )

            st.write(
                f"**Source:** "
                f"{review_ai.get('source', 'Unknown')}"
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

st.markdown(
    "### 📋 Review Audit Log"
)

review_log_path = (
    "data/review_log.json"
)


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

st.markdown(
    "## 🧪 System Evaluation"
)

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


st.markdown(
    "### Validation Results"
)


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