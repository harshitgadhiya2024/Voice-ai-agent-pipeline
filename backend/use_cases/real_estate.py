"""Real Estate Voice AI Agent — property search + booking concierge."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


REAL_ESTATE = UseCase(
    id="real_estate",
    name="Real Estate Concierge",
    company="UrbanNest Realty",
    tagline="Find your next home in seconds",
    description=(
        "A 24x7 voice concierge for property buyers and renters. Searches "
        "listings, schedules site visits, answers loan and locality questions, "
        "and qualifies leads for your sales team."
    ),
    icon="home",
    accent="emerald",
    persona_name_female="Aria",
    persona_name_male="Aarav",
    default_voice_gender="female",
    greeting=(
        "Hi, I'm Aria from UrbanNest Realty. I can help you find a home to buy "
        "or rent, schedule a site visit, or answer loan questions. What are "
        "you looking for today?"
    ),
    sample_questions=(
        "I'm looking for a 3 BHK apartment in Bandra under 4 crore",
        "Show me 2 BHK rentals in Koramangala with parking",
        "Can I schedule a site visit this Saturday morning?",
        "What home loan options do first-time buyers have?",
        "Tell me about Skyline Residences in Whitefield",
    ),
    persona=(
        "You are a warm, consultative real estate concierge for UrbanNest "
        "Realty — like a senior agent on a phone call. Listen carefully, "
        "qualify the lead politely (budget, location, BHK, timeline), and "
        "recommend matching listings from the catalog. Never invent listings "
        "that are not in the knowledge."
    ),
    fallback_disclaimer=(
        "Demo data — real listings, prices, and availability vary. For a live "
        "site visit our sales team will confirm details."
    ),
    intents=(
        IntentSpec(
            id="search_property",
            label="Property search",
            description="User wants to find a home to buy or rent.",
            required_slots=("transaction_type", "location"),
            knowledge_keys=("listings", "localities"),
            examples=(
                "Show me apartments in Powai",
                "I want to buy a 3 BHK in Whitefield",
            ),
        ),
        IntentSpec(
            id="schedule_visit",
            label="Schedule site visit",
            description="Book a tour of a specific property.",
            required_slots=("listing_id", "preferred_time"),
            knowledge_keys=("listings", "visit_policy"),
        ),
        IntentSpec(
            id="loan_assist",
            label="Home loan",
            description="Loan eligibility, EMI, banking partners.",
            required_slots=("budget_inr",),
            knowledge_keys=("loan_partners", "eligibility"),
        ),
        IntentSpec(
            id="locality_info",
            label="Locality / neighborhood",
            description="Schools, commute, amenities in an area.",
            required_slots=("location",),
            knowledge_keys=("localities",),
        ),
        IntentSpec(
            id="compare_offers",
            label="Offers & negotiation",
            description="Developer offers, discounts on listed projects.",
            required_slots=("listing_id",),
            knowledge_keys=("offers", "listings"),
        ),
        IntentSpec(
            id="rera_verify",
            label="RERA verification",
            description="Check project RERA registration status.",
            required_slots=("listing_id",),
            knowledge_keys=("rera_records",),
        ),
        IntentSpec(
            id="general",
            label="General",
            description="Greetings, about company, contact, FAQs.",
            knowledge_keys=("about", "contact", "faqs"),
        ),
    ),
    slots={
        "transaction_type": SlotSpec(
            id="transaction_type",
            question="Are you looking to buy or rent?",
            examples=("buy", "rent"),
        ),
        "location": SlotSpec(
            id="location",
            question="Which neighborhood or city are you considering?",
            examples=("Bandra", "Koramangala", "Whitefield"),
        ),
        "bhk": SlotSpec(
            id="bhk",
            question="How many bedrooms do you need — 1 BHK, 2 BHK, or 3 BHK?",
        ),
        "budget_inr": SlotSpec(
            id="budget_inr",
            question="What is your approximate budget range?",
        ),
        "listing_id": SlotSpec(
            id="listing_id",
            question="Which property are you interested in — do you have a "
            "listing ID or name?",
        ),
        "preferred_time": SlotSpec(
            id="preferred_time",
            question="When would you like to visit — what day and time works?",
        ),
    },
    knowledge={
        "about": {
            "company": "UrbanNest Realty",
            "founded": 2014,
            "cities": ["Mumbai", "Bangalore", "Hyderabad", "Pune"],
            "rera_verified": True,
        },
        "contact": {
            "phone": "+91-80-4000-1212",
            "email": "hello@urbannest.example",
            "hours": "9 AM to 9 PM, all days",
        },
        "listings": [
            {
                "id": "UN-MUM-2041",
                "title": "Skyline Heights, Bandra West",
                "transaction_type": "buy",
                "city": "Mumbai",
                "locality": "Bandra West",
                "bhk": 3,
                "carpet_sqft": 1450,
                "price_inr": 38500000,
                "amenities": ["sea view", "gym", "pool", "covered parking"],
                "available_from": "Immediate",
            },
            {
                "id": "UN-MUM-2055",
                "title": "Hiranandani Estate, Powai",
                "transaction_type": "buy",
                "city": "Mumbai",
                "locality": "Powai",
                "bhk": 2,
                "carpet_sqft": 980,
                "price_inr": 24000000,
                "amenities": ["lake view", "club house", "kids play area"],
                "available_from": "60 days",
            },
            {
                "id": "UN-BLR-3120",
                "title": "Brigade Cornerstone, Whitefield",
                "transaction_type": "buy",
                "city": "Bangalore",
                "locality": "Whitefield",
                "bhk": 3,
                "carpet_sqft": 1620,
                "price_inr": 21500000,
                "amenities": ["IT park 1km", "rooftop deck", "EV charging"],
                "available_from": "Ready to move",
            },
            {
                "id": "UN-BLR-3144",
                "title": "Prestige Lakeside, Sarjapur",
                "transaction_type": "rent",
                "city": "Bangalore",
                "locality": "Sarjapur",
                "bhk": 2,
                "carpet_sqft": 1100,
                "monthly_rent_inr": 42000,
                "deposit_inr": 250000,
                "amenities": ["semi furnished", "gym", "swimming pool"],
                "available_from": "1 Aug",
            },
            {
                "id": "UN-HYD-5012",
                "title": "My Home Avatar, Narsingi",
                "transaction_type": "buy",
                "city": "Hyderabad",
                "locality": "Narsingi",
                "bhk": 4,
                "carpet_sqft": 2450,
                "price_inr": 32000000,
                "amenities": ["clubhouse", "ORR access", "gated"],
                "available_from": "Ready to move",
            },
            {
                "id": "UN-PUN-7008",
                "title": "Kalpataru Jade Residences, Baner",
                "transaction_type": "rent",
                "city": "Pune",
                "locality": "Baner",
                "bhk": 3,
                "carpet_sqft": 1380,
                "monthly_rent_inr": 58000,
                "deposit_inr": 350000,
                "amenities": ["fully furnished", "modular kitchen", "parking 2"],
                "available_from": "Immediate",
            },
        ],
        "localities": {
            "Bandra West": {
                "vibe": "Upscale, sea-facing, F&B and shopping hub",
                "commute": "Bandra station 1.2 km, Western Express Highway 2 km",
                "schools": ["Cathedral", "Dhirubhai Ambani International"],
                "avg_price_per_sqft": 38000,
            },
            "Powai": {
                "vibe": "Lake-side, IT/finance professionals",
                "commute": "Eastern Express Highway 3 km, Airport 10 km",
                "schools": ["Hiranandani Foundation", "IIT Powai campus"],
                "avg_price_per_sqft": 28000,
            },
            "Whitefield": {
                "vibe": "Bangalore tech belt, excellent infra",
                "commute": "ITPL 2 km, Kadugodi metro 1 km, KIA 35 km",
                "schools": ["Inventure", "Ekya", "Greenwood High"],
                "avg_price_per_sqft": 9500,
            },
            "Koramangala": {
                "vibe": "Startup hub, walkable, dense F&B",
                "commute": "ORR 4 km, MG Road 6 km",
                "schools": ["NPS Koramangala", "Bethany"],
                "avg_price_per_sqft": 13500,
            },
        },
        "loan_partners": [
            {"bank": "HDFC", "max_amount_inr": 50000000, "rate_pct": 8.6},
            {"bank": "SBI", "max_amount_inr": 75000000, "rate_pct": 8.4},
            {"bank": "ICICI", "max_amount_inr": 50000000, "rate_pct": 8.7},
            {"bank": "Axis", "max_amount_inr": 40000000, "rate_pct": 8.85},
        ],
        "eligibility": {
            "min_income_monthly_inr": 60000,
            "max_loan_to_value_pct": 80,
            "max_tenure_years": 30,
            "documents": ["PAN", "Aadhaar", "salary slips 3M", "bank statements 6M"],
        },
        "visit_policy": {
            "advance_notice_hours": 12,
            "duration_minutes": 45,
            "languages_supported": ["English", "Hindi", "Marathi", "Kannada"],
            "covid_safe": True,
        },
    },
)
