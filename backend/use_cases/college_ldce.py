"""LDCE College Voice AI Agent — wraps existing LDCE knowledge base."""
from __future__ import annotations

import json
from pathlib import Path

from use_cases.base import IntentSpec, SlotSpec, UseCase

_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "college" / "data" / "ldce.json"
)
_LDCE_DATA = json.loads(_DATA_PATH.read_text(encoding="utf-8"))


LDCE_COLLEGE = UseCase(
    id="college_ldce",
    name="College Helpdesk",
    company="L.D. College of Engineering",
    tagline="Admissions, courses, fees, hostel, placement — all by voice",
    description=(
        "A college voice helpdesk for LDCE — answers prospective student "
        "questions about admissions, branches, fees, hostel, and placements; "
        "captures lead details for the admission cell."
    ),
    icon="graduation-cap",
    accent="teal",
    persona_name_female="Priya",
    persona_name_male="Rahul",
    default_voice_gender="female",
    greeting=(
        "Hi, I'm Priya from LDCE. I can help with admissions, courses, fees, "
        "hostel, or placement at L.D. College of Engineering. What would you "
        "like to know?"
    ),
    sample_questions=(
        "What is the admission process for Computer Engineering UG?",
        "Tell me about fees for MTech",
        "Which companies recruit from LDCE?",
        "Is hostel available for girls?",
        "Where is the campus located?",
    ),
    persona=(
        "You are a warm college helpdesk assistant for LDCE. Use ONLY the "
        "knowledge below. For exact numbers (fees, dates, cutoffs) ask the "
        "student to verify on ldce.ac.in or contact the admission cell."
    ),
    fallback_disclaimer=(
        "Demo data sourced from LDCE public information — verify on ldce.ac.in."
    ),
    intents=(
        IntentSpec(
            id="general",
            label="General",
            description="Greetings, about college, contact, location.",
            knowledge_keys=("about", "stats", "contact", "quick_links"),
        ),
        IntentSpec(
            id="courses",
            label="Courses",
            description="UG / PG branches, departments.",
            required_slots=("program_level",),
            knowledge_keys=("ug_departments", "pg_programs"),
        ),
        IntentSpec(
            id="admissions",
            label="Admissions",
            description="Admission process, eligibility, dates.",
            required_slots=("program_level",),
            knowledge_keys=("admissions",),
        ),
        IntentSpec(
            id="fees",
            label="Fees",
            description="Fee structure, payment, scholarships.",
            required_slots=("program_level",),
            knowledge_keys=("fees",),
        ),
        IntentSpec(
            id="placement",
            label="Placement",
            description="Companies, packages, internships.",
            knowledge_keys=("placement",),
        ),
        IntentSpec(
            id="hostel",
            label="Hostel",
            description="Hostel accommodation, rules.",
            required_slots=("accommodation_type",),
            knowledge_keys=("facilities",),
        ),
        IntentSpec(
            id="facilities",
            label="Facilities",
            description="Library, sports, labs, canteen.",
            required_slots=("facility_name",),
            knowledge_keys=("facilities", "innovation", "student_life"),
        ),
        IntentSpec(
            id="scholarship",
            label="Scholarships",
            description="Merit, need-based, sports scholarships.",
            knowledge_keys=("scholarships", "faqs"),
        ),
        IntentSpec(
            id="cutoff_trends",
            label="Cutoffs & merit",
            description="Historical ACPC cutoffs by branch.",
            required_slots=("branch",),
            knowledge_keys=("cutoffs", "programs_expanded"),
        ),
        IntentSpec(
            id="events",
            label="Events & campus life",
            description="Techfest, sports, workshops.",
            knowledge_keys=("events", "student_life"),
        ),
        IntentSpec(
            id="outreach",
            label="Outreach / counselling",
            description="Info sessions in other cities.",
            required_slots=("city",),
            knowledge_keys=("outreach_sessions", "city_guides"),
        ),
    ),
    slots={
        "program_level": SlotSpec(
            id="program_level",
            question="Are you asking about a UG (bachelor) or PG (master / MCA) "
            "program?",
        ),
        "branch": SlotSpec(
            id="branch",
            question="Which branch — Computer, IT, Mechanical, or another?",
        ),
        "accommodation_type": SlotSpec(
            id="accommodation_type",
            question="Are you looking for boys hostel, girls hostel, or "
            "general info?",
        ),
        "facility_name": SlotSpec(
            id="facility_name",
            question="Which facility — library, sports, canteen, labs, or "
            "something else?",
        ),
        "student_category": SlotSpec(
            id="student_category",
            question="Are you a current student, prospective applicant, or "
            "parent?",
        ),
        "city": SlotSpec(
            id="city",
            question="Which city are you calling from or asking about?",
        ),
    },
    knowledge={
        "about": {
            "name": _LDCE_DATA["name"],
            "short_name": _LDCE_DATA["short_name"],
            "tagline": _LDCE_DATA["tagline"],
            "motto": _LDCE_DATA["motto"],
            "established": _LDCE_DATA["established"],
            "affiliation": _LDCE_DATA["affiliation"],
            "address": _LDCE_DATA["address"],
            "summary": _LDCE_DATA["about"],
            "website": _LDCE_DATA["website"],
        },
        "stats": _LDCE_DATA.get("stats", {}),
        "ug_departments": _LDCE_DATA.get("ug_departments", []),
        "pg_programs": _LDCE_DATA.get("pg_programs", []),
        "admissions": _LDCE_DATA.get("admissions", {}),
        "fees": _LDCE_DATA.get("fees", {}),
        "placement": _LDCE_DATA.get("placement", {}),
        "facilities": _LDCE_DATA.get("facilities", {}),
        "innovation": _LDCE_DATA.get("innovation", {}),
        "student_life": _LDCE_DATA.get("student_life", {}),
        "quick_links": _LDCE_DATA.get("quick_links", []),
        "contact": _LDCE_DATA.get("contact", {}),
    },
)
