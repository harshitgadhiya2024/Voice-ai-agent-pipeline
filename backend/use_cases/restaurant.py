"""Restaurant Reservation Voice AI Agent — table bookings + menu Q&A."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


RESTAURANT = UseCase(
    id="restaurant",
    name="Restaurant Reservations",
    company="Saffron & Stone Hospitality",
    tagline="Book a table, plan a private dining experience",
    description=(
        "A voice host for a fine-dining restaurant group. Books tables, manages "
        "private events, answers menu and dietary questions, and confirms "
        "directions and parking — all without putting callers on hold."
    ),
    icon="utensils",
    accent="amber",
    persona_name_female="Maya",
    persona_name_male="Aditya",
    default_voice_gender="male",
    greeting=(
        "Good evening, this is Maya from Saffron & Stone. Would you like to "
        "reserve a table tonight, plan a private event, or know about our menu?"
    ),
    sample_questions=(
        "Table for 4 tonight at 8 PM at the Bandra outlet",
        "Do you have a vegan tasting menu?",
        "I want to book the private dining room for 12 people on Saturday",
        "Is there valet parking at the Indiranagar branch?",
        "Cancel my reservation under name Patel",
    ),
    persona=(
        "You are a polished maitre d' for Saffron & Stone — friendly, "
        "anticipatory, and concise. Confirm guest count, time, and outlet "
        "before quoting availability. Always offer alternatives if a slot "
        "is full."
    ),
    fallback_disclaimer=(
        "Demo reservation system — real bookings will be confirmed by SMS "
        "and email after the call."
    ),
    intents=(
        IntentSpec(
            id="book_table",
            label="Table reservation",
            description="Book a regular dining table.",
            required_slots=("outlet", "party_size", "date_time"),
            knowledge_keys=("outlets", "policies"),
        ),
        IntentSpec(
            id="private_event",
            label="Private event / large group",
            description="Private dining room or full venue buyout.",
            required_slots=("outlet", "party_size", "date_time", "occasion"),
            knowledge_keys=("outlets", "private_rooms", "catering_packages"),
        ),
        IntentSpec(
            id="menu_qa",
            label="Menu and dietary",
            description="Veg/vegan/gluten-free, signature dishes, kids menu.",
            knowledge_keys=("menu",),
        ),
        IntentSpec(
            id="modify_reservation",
            label="Modify or cancel",
            description="Change party size, time, or cancel a booking.",
            required_slots=("guest_name",),
            knowledge_keys=("policies",),
        ),
        IntentSpec(
            id="check_reservation",
            label="Check reservation",
            description="Look up booking by guest name or reservation ID.",
            required_slots=("guest_name",),
            knowledge_keys=("reservations", "policies"),
        ),
        IntentSpec(
            id="catering_quote",
            label="Catering / banquet",
            description="Large party catering packages and minimum spend.",
            required_slots=("outlet", "party_size"),
            knowledge_keys=("catering_packages", "private_rooms"),
        ),
        IntentSpec(
            id="general",
            label="General / directions",
            description="Hours, parking, contact info, dress code.",
            knowledge_keys=("outlets", "policies", "faqs"),
        ),
    ),
    slots={
        "outlet": SlotSpec(
            id="outlet",
            question="Which outlet — Bandra, Indiranagar, or Connaught Place?",
        ),
        "party_size": SlotSpec(
            id="party_size",
            question="How many guests will be dining?",
        ),
        "date_time": SlotSpec(
            id="date_time",
            question="What date and time would you like?",
        ),
        "occasion": SlotSpec(
            id="occasion",
            question="Is this for a special occasion — birthday, anniversary, "
            "or corporate?",
        ),
        "guest_name": SlotSpec(
            id="guest_name",
            question="May I have the name on the reservation?",
        ),
    },
    knowledge={
        "outlets": [
            {
                "name": "Saffron & Stone — Bandra",
                "city": "Mumbai",
                "address": "Linking Road, Bandra West",
                "phone": "+91-22-2640-1010",
                "hours": "12:30–15:30, 19:00–23:30 daily",
                "capacity": 80,
                "valet": True,
                "dress_code": "Smart casual",
                "michelin_recommended": True,
            },
            {
                "name": "Saffron & Stone — Indiranagar",
                "city": "Bangalore",
                "address": "12th Main, Indiranagar",
                "phone": "+91-80-4123-7878",
                "hours": "12:30–15:30, 18:30–23:30 daily",
                "capacity": 110,
                "valet": True,
                "dress_code": "Smart casual",
            },
            {
                "name": "Saffron & Stone — Connaught Place",
                "city": "Delhi",
                "address": "Block A, Connaught Place",
                "phone": "+91-11-4040-5050",
                "hours": "12:30–15:30, 19:00–23:30 daily",
                "capacity": 95,
                "valet": True,
                "dress_code": "Smart casual",
            },
        ],
        "private_rooms": [
            {
                "outlet": "Bandra",
                "name": "The Banyan Room",
                "min_pax": 8,
                "max_pax": 16,
                "min_spend_inr": 35000,
            },
            {
                "outlet": "Indiranagar",
                "name": "The Vault",
                "min_pax": 10,
                "max_pax": 24,
                "min_spend_inr": 45000,
            },
            {
                "outlet": "Connaught Place",
                "name": "The Mughal Suite",
                "min_pax": 12,
                "max_pax": 30,
                "min_spend_inr": 60000,
            },
        ],
        "catering_packages": [
            {"id": "silver", "per_pax_inr": 1850, "courses": 4, "veg_options": 6},
            {"id": "gold", "per_pax_inr": 2750, "courses": 6, "veg_options": 9},
            {"id": "platinum", "per_pax_inr": 3950, "courses": 8, "veg_options": 12},
        ],
        "menu": {
            "signatures": [
                "Smoked Aubergine Galouti (veg)",
                "Kerala Lamb Sukka",
                "Prawn Moilee with Appam",
                "Tandoori Lobster",
                "Saffron Phirni",
            ],
            "vegan": True,
            "gluten_free": True,
            "jain": True,
            "kids_menu": True,
            "wine_pairing": True,
            "alcohol": True,
        },
        "policies": {
            "advance_booking_days": 30,
            "hold_minutes": 15,
            "cancel_free_until_hours": 4,
            "no_show_fee_inr": 500,
            "private_event_deposit_pct": 50,
        },
    },
)
