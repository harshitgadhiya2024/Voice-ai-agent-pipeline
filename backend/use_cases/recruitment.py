"""Recruitment Screening Voice AI Agent — first-round phone screen."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


RECRUITMENT = UseCase(
    id="recruitment",
    name="Recruitment Screening",
    company="TalentBridge",
    tagline="Run consistent first-round screens at scale",
    description=(
        "A voice screening agent that runs structured first-round interviews "
        "for engineering, sales, and customer-success roles. Captures answers, "
        "scores fit against the JD, and books a follow-up with the recruiter."
    ),
    icon="briefcase",
    accent="cyan",
    persona_name_female="Sara",
    persona_name_male="Ravi",
    default_voice_gender="male",
    greeting=(
        "Hi, I'm Sara from TalentBridge. I'll do a quick 5-minute screen for "
        "the role you applied to — I'll ask about your experience and "
        "expectations, and book a recruiter call if it's a fit. Ready to start?"
    ),
    sample_questions=(
        "I applied for the Senior Backend Engineer role",
        "What is the salary range for the Product Manager role?",
        "I have 6 years of experience in Python and AWS",
        "Tell me about the company culture",
        "Can we reschedule my interview to next week?",
    ),
    persona=(
        "You are a friendly, professional technical recruiter on a first-round "
        "screening call. Ask one question at a time, listen, summarize, and "
        "score against the role. Never make hiring decisions — only forward to "
        "the human recruiter with a structured note."
    ),
    fallback_disclaimer=(
        "Demo screening — final interviews and offers are scheduled by the "
        "human recruiter."
    ),
    intents=(
        IntentSpec(
            id="role_info",
            label="Role information",
            description="JD details, salary band, location, hybrid policy.",
            required_slots=("role_id",),
            knowledge_keys=("roles", "company"),
        ),
        IntentSpec(
            id="screen_candidate",
            label="Conduct screening",
            description="Walk through structured screening questions.",
            required_slots=("role_id", "years_experience"),
            knowledge_keys=("roles", "screening_rubric"),
        ),
        IntentSpec(
            id="schedule_interview",
            label="Schedule interview",
            description="Book the next-round slot with a human.",
            required_slots=("role_id", "preferred_time"),
            knowledge_keys=("interview_process",),
        ),
        IntentSpec(
            id="company_qa",
            label="Company culture / benefits",
            description="Perks, work-from-home, growth.",
            knowledge_keys=("company", "benefits"),
        ),
        IntentSpec(
            id="application_status",
            label="Application status",
            description="Where am I in the hiring pipeline.",
            required_slots=("role_id",),
            knowledge_keys=("screenings", "interviews"),
        ),
        IntentSpec(
            id="referral",
            label="Employee referral",
            description="Refer a friend, referral bonus policy.",
            knowledge_keys=("company", "benefits", "faqs"),
        ),
        IntentSpec(
            id="general",
            label="General",
            description="Application status, recruiter contact, careers page.",
            knowledge_keys=("company", "faqs"),
        ),
    ),
    slots={
        "role_id": SlotSpec(
            id="role_id",
            question="Which role did you apply to — could you share the title "
            "or job ID?",
        ),
        "years_experience": SlotSpec(
            id="years_experience",
            question="How many years of relevant experience do you have?",
        ),
        "current_ctc": SlotSpec(
            id="current_ctc",
            question="What is your current total compensation, approximately?",
        ),
        "expected_ctc": SlotSpec(
            id="expected_ctc",
            question="And what compensation are you targeting for this role?",
        ),
        "notice_period": SlotSpec(
            id="notice_period",
            question="What is your notice period, in weeks?",
        ),
        "preferred_time": SlotSpec(
            id="preferred_time",
            question="When are you free for a 45-minute follow-up?",
        ),
    },
    knowledge={
        "company": {
            "name": "TalentBridge",
            "size_employees": 850,
            "hq": "Bangalore",
            "offices": ["Bangalore", "Pune", "Singapore", "London"],
            "founded": 2017,
            "industry": "B2B SaaS - Hiring Automation",
        },
        "benefits": [
            "Hybrid (3 days office)",
            "Health insurance for family up to 10 lakh",
            "Annual learning budget 75,000",
            "ESOPs for SDE-2 and above",
            "26 days paid leave + sick",
            "Wellness stipend 2,500/month",
        ],
        "roles": [
            {
                "id": "TB-ENG-22",
                "title": "Senior Backend Engineer",
                "team": "Platform",
                "location": "Bangalore (hybrid)",
                "experience_years": "5-9",
                "must_have": ["Python", "Postgres", "AWS", "system design"],
                "nice_to_have": ["Go", "Kafka", "Kubernetes"],
                "salary_band_inr_lpa": "32-52",
            },
            {
                "id": "TB-PM-08",
                "title": "Senior Product Manager",
                "team": "Search & Matching",
                "location": "Bangalore (hybrid)",
                "experience_years": "6-10",
                "must_have": ["B2B SaaS", "data-driven decisions", "roadmap ownership"],
                "salary_band_inr_lpa": "42-65",
            },
            {
                "id": "TB-CS-14",
                "title": "Customer Success Manager",
                "team": "Enterprise CS",
                "location": "Pune (hybrid)",
                "experience_years": "3-6",
                "must_have": ["enterprise account management", "QBRs", "Salesforce"],
                "salary_band_inr_lpa": "18-28",
            },
        ],
        "screening_rubric": {
            "engineering": [
                "Recent project depth + impact",
                "Strongest tech and weakest tech",
                "System design exposure",
                "Notice period",
                "Comp expectation",
            ],
            "product": [
                "Highest-impact PM project",
                "Discovery vs delivery balance",
                "Stakeholder management example",
                "PRD writing process",
                "Comp expectation",
            ],
            "customer_success": [
                "Largest book of business",
                "QBR cadence and tooling",
                "Churn save story",
                "Comp expectation",
            ],
        },
        "interview_process": {
            "rounds": [
                "Recruiter screen (this call)",
                "Technical / Case round (90 min)",
                "Hiring manager (60 min)",
                "Cross-functional bar raiser (45 min)",
                "Offer + reference check",
            ],
            "avg_duration_days": 14,
        },
    },
)
