"""AI Travel Planner Voice AI Agent — flight + stay + itinerary."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


TRAVEL = UseCase(
    id="travel",
    name="Travel Planner",
    company="WanderWave Travel",
    tagline="Plan, book, and manage trips by voice",
    description=(
        "A full-service travel concierge — searches flights and hotels, "
        "assembles itineraries, applies loyalty programs, and rebooks during "
        "disruptions. Designed for both leisure and corporate travel."
    ),
    icon="plane",
    accent="violet",
    persona_name_female="Tara",
    persona_name_male="Kabir",
    default_voice_gender="male",
    greeting=(
        "Hi, this is Tara from WanderWave. I can plan a trip, book a flight "
        "or hotel, build an itinerary, or sort out a delay. Where are you "
        "headed?"
    ),
    sample_questions=(
        "I want to fly Bangalore to Bali for a week in October",
        "Find me a 4-star hotel near Colaba under 12000 a night",
        "Build me a 5-day Japan itinerary for two adults",
        "My flight got cancelled — please rebook me",
        "Book a cab for tomorrow 6 AM, Delhi airport",
    ),
    persona=(
        "You are a thoughtful travel planner — listen to the brief, ask only "
        "the questions you actually need (origin, dates, traveller count, "
        "vibe), and propose 2-3 solid options instead of overwhelming the "
        "caller. Always show prices in INR with date ranges."
    ),
    fallback_disclaimer=(
        "Demo flight and hotel data — real fares vary by inventory and "
        "currency in production."
    ),
    intents=(
        IntentSpec(
            id="search_flight",
            label="Flight search",
            description="One-way / round-trip / multi-city flights.",
            required_slots=("origin", "destination", "depart_date"),
            knowledge_keys=("flights", "airlines"),
        ),
        IntentSpec(
            id="search_hotel",
            label="Hotel search",
            description="Stay search by city + dates + budget.",
            required_slots=("destination", "check_in", "check_out"),
            knowledge_keys=("hotels",),
        ),
        IntentSpec(
            id="build_itinerary",
            label="Plan itinerary",
            description="Multi-day plan with attractions + transport.",
            required_slots=("destination", "trip_length_days", "trip_vibe"),
            knowledge_keys=("destinations", "experiences"),
        ),
        IntentSpec(
            id="manage_booking",
            label="Manage existing booking",
            description="Cancel, reschedule, web check-in.",
            required_slots=("booking_id",),
            knowledge_keys=("policies",),
        ),
        IntentSpec(
            id="disruption",
            label="Flight disruption",
            description="Delays, cancellations, rebooking.",
            required_slots=("booking_id",),
            knowledge_keys=("policies", "disruption_sla"),
        ),
        IntentSpec(
            id="visa_info",
            label="Visa requirements",
            description="Tourist/business visa processing times and fees.",
            required_slots=("destination",),
            knowledge_keys=("visas", "destinations"),
        ),
        IntentSpec(
            id="package_deal",
            label="Flight + hotel package",
            description="Bundled holiday packages and experiences.",
            required_slots=("destination", "trip_length_days"),
            knowledge_keys=("experiences", "hotels", "flights"),
        ),
        IntentSpec(
            id="general",
            label="General",
            description="Visas, currency, contact info, policies.",
            knowledge_keys=("about", "faqs", "policies"),
        ),
    ),
    slots={
        "origin": SlotSpec(
            id="origin",
            question="Where are you flying from?",
        ),
        "destination": SlotSpec(
            id="destination",
            question="Where would you like to go?",
        ),
        "depart_date": SlotSpec(
            id="depart_date",
            question="What date would you like to depart?",
        ),
        "return_date": SlotSpec(
            id="return_date",
            question="And the return date?",
        ),
        "travellers": SlotSpec(
            id="travellers",
            question="How many travellers — adults and children?",
        ),
        "check_in": SlotSpec(
            id="check_in",
            question="What is your hotel check-in date?",
        ),
        "check_out": SlotSpec(
            id="check_out",
            question="And the check-out date?",
        ),
        "trip_length_days": SlotSpec(
            id="trip_length_days",
            question="How many days will the trip be?",
        ),
        "trip_vibe": SlotSpec(
            id="trip_vibe",
            question="What kind of trip — adventure, leisure, romance, "
            "or family?",
        ),
        "booking_id": SlotSpec(
            id="booking_id",
            question="Could you share the booking ID — usually starts with WW-?",
        ),
    },
    knowledge={
        "about": {
            "company": "WanderWave Travel",
            "founded": 2012,
            "iata_accredited": True,
            "support_24x7": True,
        },
        "loyalty": {
            "name": "WanderWave Wings",
            "earn_pct": 1.5,
            "redeem_min_points": 5000,
            "tier_perks": [
                "Silver: priority email",
                "Gold: free hotel upgrade subject to availability",
                "Platinum: dedicated travel desk + lounge access vouchers",
            ],
        },
        "airlines": ["IndiGo", "Air India", "Vistara", "Singapore Airlines", "Emirates"],
        "flights": [
            {
                "from": "BLR",
                "to": "DPS",
                "airline": "Singapore Airlines",
                "depart": "2026-10-12 22:10",
                "arrive": "2026-10-13 11:40",
                "fare_inr": 38500,
                "stops": 1,
                "via": "SIN",
                "baggage_kg": 30,
            },
            {
                "from": "BLR",
                "to": "DPS",
                "airline": "IndiGo",
                "depart": "2026-10-12 06:25",
                "arrive": "2026-10-12 17:55",
                "fare_inr": 28900,
                "stops": 1,
                "via": "KUL",
                "baggage_kg": 25,
            },
            {
                "from": "DEL",
                "to": "NRT",
                "airline": "Air India",
                "depart": "2026-09-04 21:30",
                "arrive": "2026-09-05 11:25",
                "fare_inr": 64200,
                "stops": 0,
                "baggage_kg": 30,
            },
        ],
        "hotels": [
            {
                "city": "Bali",
                "name": "Padma Resort Legian",
                "stars": 5,
                "per_night_inr": 14500,
                "amenities": ["beachfront", "pool", "spa"],
            },
            {
                "city": "Bali",
                "name": "Alaya Ubud",
                "stars": 4,
                "per_night_inr": 9800,
                "amenities": ["rice-field view", "yoga", "pool"],
            },
            {
                "city": "Mumbai",
                "name": "The Resort Madh-Marve",
                "stars": 4,
                "per_night_inr": 11500,
                "amenities": ["pool", "beach 5 min", "kid friendly"],
            },
            {
                "city": "Tokyo",
                "name": "Hotel Gracery Shinjuku",
                "stars": 4,
                "per_night_inr": 18800,
                "amenities": ["central", "metro 200m"],
            },
        ],
        "destinations": {
            "Bali": {
                "best_months": ["Apr", "May", "Jun", "Sep", "Oct"],
                "vibe": "Beach + cultural mix; Ubud for chill, Seminyak for nightlife",
                "visa": "Visa on arrival 30 days for Indian passport",
            },
            "Japan": {
                "best_months": ["Mar", "Apr", "Oct", "Nov"],
                "vibe": "Tokyo + Kyoto + Osaka; cherry blossom or autumn foliage",
                "visa": "eVisa required for Indian passport",
            },
            "Goa": {
                "best_months": ["Nov", "Dec", "Jan", "Feb"],
                "vibe": "North Goa for nightlife, South for quiet beaches",
                "visa": "Domestic — no visa",
            },
        },
        "experiences": [
            {"city": "Bali", "name": "Mount Batur Sunrise Trek", "duration_h": 7, "price_inr": 4500},
            {"city": "Bali", "name": "Tegallalang Rice Terraces tour", "duration_h": 4, "price_inr": 2200},
            {"city": "Tokyo", "name": "TeamLab Borderless", "duration_h": 3, "price_inr": 2400},
            {"city": "Tokyo", "name": "Mt Fuji day trip", "duration_h": 12, "price_inr": 6800},
            {"city": "Goa", "name": "Catamaran Sunset Cruise", "duration_h": 2, "price_inr": 1800},
        ],
        "policies": {
            "free_cancel_window_hours": 24,
            "rebooking_fee_inr": 500,
            "name_change_allowed": False,
            "web_checkin_open_hours": 48,
        },
        "disruption_sla": {
            "rebook_within_minutes": 30,
            "compensation_under_dgca": True,
            "refund_eligible_categories": ["airline cancel", "schedule change >2h"],
        },
    },
)
