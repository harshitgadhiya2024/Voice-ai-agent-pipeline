"""AI Debt Collection Voice AI Agent — compliant, empathetic outreach."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


DEBT_COLLECTION = UseCase(
    id="debt_collection",
    name="Debt Collection",
    company="Avenir Recoveries",
    tagline="Compliant, empathetic outreach — no scripts that pressure",
    description=(
        "A regulator-compliant collections voice agent. Verifies identity, "
        "explains the dues calmly, offers payment plans, and either captures "
        "a commitment or warm-transfers to a human — fully audited."
    ),
    icon="receipt",
    accent="orange",
    persona_name_female="Meera",
    persona_name_male="Arjun",
    default_voice_gender="male",
    greeting=(
        "Hello, this is Meera from Avenir Recoveries calling on behalf of "
        "Meridian Bank. Before we discuss your account, may I confirm I'm "
        "speaking with the account holder?"
    ),
    sample_questions=(
        "I'm not sure why I'm being called",
        "I can pay 5000 today, can we set up a plan for the rest?",
        "Please don't call me at work",
        "I want to dispute this — I already paid last month",
        "What is the total amount outstanding?",
    ),
    persona=(
        "You are a calm, empathetic collections agent — never threatening, "
        "never pressuring. Verify the customer is the account holder before "
        "discussing any details. Quote regulator-compliant language only. "
        "If the customer asks not to be contacted, log the request and end "
        "politely. If they dispute the debt, pause collection and route to "
        "a human."
    ),
    fallback_disclaimer=(
        "Demo data — production deployments must comply with RBI Fair "
        "Practice Code and FDCPA-style call recording / Do Not Call rules."
    ),
    intents=(
        IntentSpec(
            id="verify_account",
            label="Verify account holder",
            description="Confirm right person before talking dues.",
            required_slots=("account_id", "verification"),
            knowledge_keys=("compliance",),
        ),
        IntentSpec(
            id="explain_dues",
            label="Explain outstanding",
            description="Walk through what is owed and why.",
            required_slots=("account_id",),
            knowledge_keys=("accounts", "compliance"),
        ),
        IntentSpec(
            id="payment_plan",
            label="Offer payment plan",
            description="Negotiate amount + schedule.",
            required_slots=("account_id", "amount_offered"),
            knowledge_keys=("accounts", "payment_plans"),
        ),
        IntentSpec(
            id="dispute",
            label="Customer dispute",
            description="Customer disagrees — pause and escalate.",
            required_slots=("account_id", "dispute_reason"),
            knowledge_keys=("compliance", "dispute_routing"),
        ),
        IntentSpec(
            id="dnc",
            label="Do-not-contact request",
            description="Customer asks not to be contacted.",
            knowledge_keys=("compliance",),
        ),
        IntentSpec(
            id="settlement_offer",
            label="Settlement offer",
            description="One-time settlement or waiver programs.",
            required_slots=("account_id",),
            knowledge_keys=("settlements", "payment_plans"),
        ),
        IntentSpec(
            id="schedule_callback",
            label="Schedule callback",
            description="Customer asks to be called back later.",
            required_slots=("account_id",),
            knowledge_keys=("callbacks", "compliance"),
        ),
        IntentSpec(
            id="hardship",
            label="Financial hardship",
            description="Job loss, medical — temporary relief options.",
            required_slots=("account_id",),
            knowledge_keys=("payment_plans", "compliance"),
        ),
        IntentSpec(
            id="general",
            label="General",
            description="Hours, contact, regulator info.",
            knowledge_keys=("about", "compliance", "faqs"),
        ),
    ),
    slots={
        "account_id": SlotSpec(
            id="account_id",
            question="May I have your account or loan reference number for "
            "verification?",
        ),
        "verification": SlotSpec(
            id="verification",
            question="To confirm I'm speaking with the right person, could you "
            "share your date of birth?",
        ),
        "amount_offered": SlotSpec(
            id="amount_offered",
            question="What amount can you comfortably pay today, and what "
            "schedule works for the balance?",
        ),
        "dispute_reason": SlotSpec(
            id="dispute_reason",
            question="Could you share what you believe is incorrect — was it "
            "already paid, an unauthorised charge, or something else?",
        ),
    },
    knowledge={
        "about": {
            "agency": "Avenir Recoveries",
            "client_types": ["Banks", "NBFCs", "Telecoms"],
            "founded": 2015,
            "regulator_registration": "RBI BC code AR-9921",
        },
        "compliance": {
            "calling_window": "08:00 to 19:00 local time",
            "max_calls_per_day": 2,
            "language_rules": "No threats, no abuse, no calls to family or employers",
            "id_verification_required": True,
            "recording_required": True,
            "complaint_email": "complaints@avenir.example",
            "complaint_phone": "+91-22-6900-9000",
            "regulator": "RBI Fair Practice Code",
        },
        "accounts": [
            {
                "id": "ML-991023",
                "type": "Home Loan EMI overdue",
                "principal_inr": 6500000,
                "overdue_emi_inr": 52340,
                "overdue_days": 18,
                "late_fee_inr": 850,
                "client": "Meridian Bank",
            },
            {
                "id": "CC-77554",
                "type": "Credit Card outstanding",
                "outstanding_inr": 47820,
                "overdue_days": 42,
                "min_due_inr": 2400,
                "late_fee_inr": 1200,
                "client": "Meridian Bank",
            },
        ],
        "payment_plans": [
            {"id": "P1", "down_pay_pct": 25, "tenure_months": 3, "rate_pct": 0},
            {"id": "P2", "down_pay_pct": 10, "tenure_months": 6, "rate_pct": 4},
            {"id": "P3", "down_pay_pct": 0, "tenure_months": 9, "rate_pct": 8},
        ],
        "dispute_routing": {
            "auto_pause_days": 10,
            "human_team": "Avenir L2 Disputes",
            "callback_within_business_days": 3,
        },
    },
)
