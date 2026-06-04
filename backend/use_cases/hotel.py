"""Hotel Booking Voice AI Agent — reservations + concierge."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


HOTEL = UseCase(
    id="hotel",
    name="Hotel Booking & Concierge",
    company="Tirtha Hotels & Resorts",
    tagline="Book a stay, request a service, plan your trip",
    description=(
        "A 24x7 voice front-desk agent for a boutique hotel chain. Handles "
        "room search and bookings, in-stay requests (housekeeping, F&B), and "
        "concierge questions like spa, transport, and tours."
    ),
    icon="bed",
    accent="rose",
    persona_name_female="Naina",
    persona_name_male="Vikram",
    default_voice_gender="female",
    greeting=(
        "Welcome to Tirtha Hotels, this is Naina. I can help you book a stay, "
        "request a service, or plan a tour — how may I assist you?"
    ),
    sample_questions=(
        "Book a deluxe room in our Goa property from 12 to 15 June, 2 adults",
        "Send extra towels to room 412 please",
        "What time is breakfast served at the Udaipur property?",
        "Arrange airport pickup for tomorrow 9 AM, Mumbai",
        "Cancel my booking under reference TIR-9008",
    ),
    persona=(
        "You are a warm hotel front-desk agent — anticipatory, polite, and "
        "calm. Confirm dates, property, and guest count before quoting. Use "
        "guest names where known. Never invent properties or rates not in the "
        "knowledge."
    ),
    fallback_disclaimer=(
        "Demo data — real bookings are confirmed by email and synced to your "
        "PMS in production."
    ),
    intents=(
        IntentSpec(
            id="search_room",
            label="Room search and booking",
            description="Check availability and book.",
            required_slots=("property", "check_in", "check_out", "guests"),
            knowledge_keys=("properties", "rates", "bookings", "policies"),
        ),
        IntentSpec(
            id="modify_booking",
            label="Modify or cancel",
            description="Change dates, upgrade, or cancel.",
            required_slots=("booking_id",),
            knowledge_keys=("policies",),
        ),
        IntentSpec(
            id="in_stay_request",
            label="In-stay service",
            description="Housekeeping, F&B, maintenance.",
            required_slots=("room_number", "request_type"),
            knowledge_keys=("services", "in_stay_sla"),
        ),
        IntentSpec(
            id="concierge",
            label="Concierge / experiences",
            description="Spa, tours, transport, dining recommendations.",
            knowledge_keys=("experiences", "transport"),
        ),
        IntentSpec(
            id="loyalty_redeem",
            label="Loyalty & points",
            description="Redeem points, tier benefits, upgrades.",
            knowledge_keys=("loyalty", "faqs"),
        ),
        IntentSpec(
            id="group_booking",
            label="Group / wedding block",
            description="Block rooms for events or corporate groups.",
            required_slots=("property", "guests"),
            knowledge_keys=("properties", "policies"),
        ),
        IntentSpec(
            id="general",
            label="General",
            description="Hours, contact, loyalty programme.",
            knowledge_keys=("about", "loyalty", "faqs"),
        ),
    ),
    slots={
        "property": SlotSpec(
            id="property",
            question="Which property — Goa, Udaipur, or Coorg?",
        ),
        "check_in": SlotSpec(
            id="check_in",
            question="What is your check-in date?",
        ),
        "check_out": SlotSpec(
            id="check_out",
            question="And the check-out date?",
        ),
        "guests": SlotSpec(
            id="guests",
            question="How many adults and children will be staying?",
        ),
        "booking_id": SlotSpec(
            id="booking_id",
            question="Could you share the booking reference — it starts with TIR-?",
        ),
        "room_number": SlotSpec(
            id="room_number",
            question="Which room are you in — could you share the room number?",
        ),
        "request_type": SlotSpec(
            id="request_type",
            question="What service do you need — housekeeping, F&B, maintenance, "
            "or something else?",
        ),
    },
    knowledge={
        "about": {
            "brand": "Tirtha Hotels & Resorts",
            "founded": 2008,
            "properties_count": 6,
            "categories": ["Luxury", "Heritage", "Wellness"],
        },
        "loyalty": {
            "name": "Tirtha Circle",
            "tiers": ["Silver (5 nights)", "Gold (15 nights)", "Platinum (30 nights)"],
            "benefits": [
                "Room upgrade subject to availability",
                "Late checkout 2 PM",
                "Welcome drink + handcrafted amenity",
                "Complimentary breakfast (Gold and above)",
            ],
        },
        "properties": [
            {
                "id": "tirtha-goa",
                "name": "Tirtha Goa — Villas by the Sea",
                "city": "North Goa",
                "rooms": ["Garden Villa", "Pool Villa", "Sea-view Suite"],
                "check_in_time": "14:00",
                "check_out_time": "12:00",
                "amenities": ["pool", "spa", "beach access", "kids club"],
            },
            {
                "id": "tirtha-udaipur",
                "name": "Tirtha Udaipur — Palace Wing",
                "city": "Udaipur",
                "rooms": ["Heritage Room", "Lake-view Suite", "Maharaja Suite"],
                "check_in_time": "14:00",
                "check_out_time": "12:00",
                "amenities": ["lake view", "boat ride", "ayurveda spa"],
            },
            {
                "id": "tirtha-coorg",
                "name": "Tirtha Coorg — Coffee Estate",
                "city": "Coorg",
                "rooms": ["Estate Room", "Plantation Cottage", "Hillside Villa"],
                "check_in_time": "13:00",
                "check_out_time": "11:00",
                "amenities": ["estate walk", "trekking", "wellness retreat"],
            },
        ],
        "rates": {
            "tirtha-goa": {
                "Garden Villa": 18500,
                "Pool Villa": 32000,
                "Sea-view Suite": 26000,
            },
            "tirtha-udaipur": {
                "Heritage Room": 22000,
                "Lake-view Suite": 38000,
                "Maharaja Suite": 75000,
            },
            "tirtha-coorg": {
                "Estate Room": 14500,
                "Plantation Cottage": 21000,
                "Hillside Villa": 28000,
            },
            "currency": "INR",
            "tax_pct": 18,
            "breakfast_included": True,
        },
        "policies": {
            "free_cancel_until_hours": 48,
            "pet_friendly_properties": ["tirtha-coorg"],
            "child_under_age_free": 6,
            "id_required": True,
        },
        "services": [
            "Housekeeping",
            "Laundry (express + regular)",
            "In-room dining",
            "Maintenance",
            "Doctor on call",
            "Wake-up call",
        ],
        "in_stay_sla": {
            "housekeeping_minutes": 15,
            "in_room_dining_minutes": 25,
            "maintenance_minutes": 20,
            "doctor_on_call_minutes": 30,
        },
        "experiences": [
            {"name": "Sunset Catamaran (Goa)", "duration_min": 90, "price_inr": 4500, "max_pax": 6},
            {"name": "Lake Pichola Boat (Udaipur)", "duration_min": 60, "price_inr": 1800, "max_pax": 8},
            {"name": "Coffee Plantation Walk (Coorg)", "duration_min": 75, "price_inr": 1200, "max_pax": 10},
            {"name": "Ayurveda Massage (60 min)", "duration_min": 60, "price_inr": 4200, "max_pax": 1},
        ],
        "transport": {
            "airport_pickup_inr": {"Goa": 1800, "Udaipur": 1500, "Coorg": 4500},
            "self_drive_partner": "Zoomcar (member rate)",
            "chauffeur_per_day_inr": 3500,
        },
    },
)
