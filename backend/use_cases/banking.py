"""Banking Support Voice AI Agent — retail banking customer service."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


BANKING = UseCase(
    id="banking",
    name="Banking Support",
    company="Meridian Bank",
    tagline="Account, cards, loans — handled in one call",
    description=(
        "A retail-banking voice agent for account questions, card actions "
        "(block, replace, limits), loan EMI queries, and dispute logging — "
        "with strong identity verification and policy-safe answers."
    ),
    icon="landmark",
    accent="sky",
    persona_name_female="Anjali",
    persona_name_male="Rohan",
    default_voice_gender="male",
    greeting=(
        "Welcome to Meridian Bank, this is Anjali. For your security I'll "
        "verify a few details before we begin. How can I help you today — "
        "account, cards, or loans?"
    ),
    sample_questions=(
        "What is the balance on my savings account ending 4421?",
        "I lost my debit card, please block it",
        "What is the EMI left on my home loan ML-991023?",
        "Status of cheque I deposited last week",
        "I got a suspicious UPI link — is it fraud?",
        "Nearest Meridian branch IFSC in Pune",
    ),
    persona=(
        "You are a calm, secure banking voice agent. Always verify identity "
        "(last 4 of card, date of birth, registered phone) before performing "
        "an action. Never read full account numbers — only last 4 digits. "
        "Never share OTPs or PINs. For high-risk actions (>₹50,000 transfers, "
        "loan disbursal) explicitly confirm and route to a human banker."
    ),
    fallback_disclaimer=(
        "Demo data — real account access requires multi-factor authentication "
        "and is logged for audit."
    ),
    intents=(
        IntentSpec(
            id="account_info",
            label="Account info",
            description="Balance, recent transactions, statements.",
            required_slots=("account_last4", "verification"),
            knowledge_keys=("accounts", "transactions", "policies"),
        ),
        IntentSpec(
            id="card_action",
            label="Card actions",
            description="Block, replace, limit change, hotlist.",
            required_slots=("card_last4", "card_action"),
            knowledge_keys=("cards", "policies"),
        ),
        IntentSpec(
            id="loan_qa",
            label="Loan information",
            description="EMI, foreclosure, top-up.",
            required_slots=("loan_id",),
            knowledge_keys=("loans",),
        ),
        IntentSpec(
            id="dispute",
            label="Transaction dispute",
            description="Raise unauthorised or duplicate charge.",
            required_slots=("transaction_ref",),
            knowledge_keys=("dispute_policy",),
        ),
        IntentSpec(
            id="cheque_status",
            label="Cheque status",
            description="Clearing, bounce, stop-payment on cheques.",
            required_slots=("account_last4",),
            knowledge_keys=("cheques", "policies"),
        ),
        IntentSpec(
            id="investment_faq",
            label="Deposits & investments",
            description="FD, RD, mutual funds, PPF eligibility.",
            knowledge_keys=("investments", "fees"),
        ),
        IntentSpec(
            id="fraud_report",
            label="Fraud / phishing",
            description="Report scam SMS, UPI fraud, card skimming.",
            knowledge_keys=("fraud_cases", "policies"),
        ),
        IntentSpec(
            id="atm_locator",
            label="ATM / branch locator",
            description="Find ATM or branch by city.",
            required_slots=("city",),
            knowledge_keys=("atms", "branches"),
        ),
        IntentSpec(
            id="general",
            label="General / branch",
            description="Branch hours, IFSC, contact, fees.",
            knowledge_keys=("branches", "fees", "faqs"),
        ),
    ),
    slots={
        "account_last4": SlotSpec(
            id="account_last4",
            question="Could you share the last 4 digits of your account number?",
        ),
        "verification": SlotSpec(
            id="verification",
            question="For verification, may I have your date of birth and "
            "registered mobile number?",
        ),
        "card_last4": SlotSpec(
            id="card_last4",
            question="Last 4 digits of the card, please?",
        ),
        "card_action": SlotSpec(
            id="card_action",
            question="What would you like to do — block, hotlist, replace, "
            "or change limit?",
        ),
        "loan_id": SlotSpec(
            id="loan_id",
            question="Could you share the loan account number — it usually "
            "starts with ML or PL?",
        ),
        "transaction_ref": SlotSpec(
            id="transaction_ref",
            question="Could you share the transaction reference number or the "
            "date and amount?",
        ),
        "city": SlotSpec(
            id="city",
            question="Which city should I look up — branch or ATM?",
        ),
    },
    knowledge={
        "about": {
            "bank": "Meridian Bank",
            "founded": 1998,
            "branches": 1240,
            "atms": 4200,
            "regulator": "Reserve Bank of India",
        },
        "branches": [
            {"city": "Mumbai", "name": "Bandra Kurla Complex", "ifsc": "MERI0000211", "hours": "9:30–17:30 weekdays"},
            {"city": "Bangalore", "name": "Indiranagar", "ifsc": "MERI0000412", "hours": "9:30–17:30 weekdays"},
            {"city": "Delhi", "name": "Connaught Place", "ifsc": "MERI0000101", "hours": "9:30–17:30 weekdays"},
        ],
        "accounts": [
            {
                "last4": "4421",
                "type": "Savings",
                "balance_inr": 287430.55,
                "linked_phone_last2": "82",
                "recent_transactions": [
                    {"date": "2026-06-02", "desc": "UPI to Zomato", "amount_inr": -740, "ref": "TXN9981231"},
                    {"date": "2026-05-31", "desc": "Salary credit", "amount_inr": 145000, "ref": "TXN9978002"},
                    {"date": "2026-05-28", "desc": "Auto-debit Netflix", "amount_inr": -649, "ref": "TXN9974190"},
                ],
            },
            {
                "last4": "8809",
                "type": "Current",
                "balance_inr": 1240992.10,
                "linked_phone_last2": "33",
                "recent_transactions": [
                    {"date": "2026-06-01", "desc": "RTGS out", "amount_inr": -250000, "ref": "TXN9982002"}
                ],
            },
        ],
        "cards": [
            {"last4": "1212", "network": "Visa", "type": "Credit", "limit_inr": 500000, "available_inr": 312500, "expiry": "08/2029"},
            {"last4": "7755", "network": "Mastercard", "type": "Debit", "daily_limit_inr": 200000, "expiry": "11/2027"},
        ],
        "loans": [
            {
                "id": "ML-991023",
                "type": "Home Loan",
                "principal_inr": 6500000,
                "outstanding_inr": 4385412,
                "emi_inr": 52340,
                "rate_pct": 8.6,
                "tenure_months_left": 224,
                "next_emi_on": "2026-06-05",
            },
            {
                "id": "PL-118822",
                "type": "Personal Loan",
                "principal_inr": 800000,
                "outstanding_inr": 322110,
                "emi_inr": 18950,
                "rate_pct": 11.5,
                "tenure_months_left": 18,
                "next_emi_on": "2026-06-10",
            },
        ],
        "fees": {
            "non_maintenance_savings_inr": 250,
            "atm_other_bank_after_5_inr": 21,
            "rtgs_above_2lakh_inr": 25,
            "duplicate_statement_inr": 100,
        },
        "dispute_policy": {
            "raise_within_days": 60,
            "credit_card_chargeback_days": 120,
            "provisional_credit_within_days": 7,
            "investigation_business_days": 30,
        },
        "policies": {
            "card_block_immediate": True,
            "replacement_card_business_days": "5-7",
            "limit_change_max_pct": 50,
            "high_value_transfer_human_review_inr": 500000,
        },
    },
)
