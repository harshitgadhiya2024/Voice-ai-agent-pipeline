#!/usr/bin/env python3
"""Generate 1000+ knowledge records PER domain for all voicebot demos.

Run from backend/:
  conda run -n base python scripts/generate_knowledge_data.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

OUT = Path(__file__).resolve().parent.parent / "use_cases" / "data"
MIN_RECORDS = 1050
random.seed(42)

CITIES = [
    ("Mumbai", "Maharashtra", "MERI"),
    ("Pune", "Maharashtra", "MERI"),
    ("Bangalore", "Karnataka", "MERI"),
    ("Hyderabad", "Telangana", "MERI"),
    ("Delhi", "Delhi", "MERI"),
    ("Ahmedabad", "Gujarat", "MERI"),
    ("Chennai", "Tamil Nadu", "MERI"),
    ("Kolkata", "West Bengal", "MERI"),
    ("Jaipur", "Rajasthan", "MERI"),
    ("Surat", "Gujarat", "MERI"),
    ("Noida", "Uttar Pradesh", "MERI"),
    ("Gurugram", "Haryana", "MERI"),
    ("Kochi", "Kerala", "MERI"),
    ("Chandigarh", "Chandigarh", "MERI"),
    ("Indore", "Madhya Pradesh", "MERI"),
    ("Lucknow", "Uttar Pradesh", "MERI"),
    ("Bhopal", "Madhya Pradesh", "MERI"),
    ("Nagpur", "Maharashtra", "MERI"),
    ("Vadodara", "Gujarat", "MERI"),
    ("Coimbatore", "Tamil Nadu", "MERI"),
]

LOCALITIES = [
    "Central", "West", "East", "North", "South", "IT Corridor",
    "Old City", "Airport Road", "Lakefront", "Metro Hub",
]

BHK = [1, 2, 3, 4, 5]
AIRPORTS = [
    "DEL", "BOM", "BLR", "HYD", "MAA", "CCU", "AMD", "PNQ", "GOI", "COK",
    "JAI", "LKO", "BBI", "TRV", "IXC", "DPS", "BKK", "SIN", "DXB", "LHR",
]
BRANCHES_ENG = [
    "Computer Engineering", "Information Technology", "Mechanical Engineering",
    "Civil Engineering", "Electrical Engineering", "Electronics and Communication",
    "Chemical Engineering", "Automobile Engineering", "Biomedical Engineering",
]


def _count_records(data: dict[str, Any]) -> int:
    total = 0
    for key, val in data.items():
        if key == "meta":
            continue
        if isinstance(val, list):
            total += len(val)
        elif isinstance(val, dict):
            for sub_k, sub_v in val.items():
                if isinstance(sub_v, list):
                    total += len(sub_v)
                elif isinstance(sub_v, dict):
                    total += len(sub_v)
    return total


def _write(name: str, data: dict[str, Any]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    n = _count_records(data)
    data["meta"] = {
        "record_count": n,
        "version": "3.0",
        "min_target": MIN_RECORDS,
        "coverage": "multi-city India · expanded scenarios",
    }
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    status = "OK" if n >= MIN_RECORDS else "LOW"
    print(f"  {name}.json — {n:,} records [{status}]")
    return n


def _faqs(domain: str, topics: list[str], each: int = 8) -> list[dict]:
    out = []
    i = 0
    for topic in topics:
        for j in range(each):
            i += 1
            out.append({
                "id": f"FAQ-{domain[:3].upper()}-{i:04d}",
                "topic": topic,
                "q": f"{topic} — scenario {j + 1}?",
                "a": f"Policy and steps for {topic.lower()} case {j + 1} in {domain}.",
            })
    return out


# ---------------------------------------------------------------------------
# Real estate — listings drive count
# ---------------------------------------------------------------------------
def gen_real_estate() -> dict[str, Any]:
    listings = []
    lid = 10000
    builders = ["Skyline", "Green Valley", "Urban Crest", "Lake View", "Metro Heights", "Palm Grove"]
    for city, state, _ in CITIES:
        for locality in LOCALITIES:
            for bhk in BHK:
                for txn in ("buy", "rent"):
                    for variant in range(3):
                        lid += 1
                        rent = 12000 + bhk * 11000 + random.randint(0, 12000)
                        price = (6 + bhk * 3 + random.randint(0, 8)) * 1_000_000
                        listings.append({
                            "id": f"UN-{city[:3].upper()}-{lid}",
                            "title": f"{random.choice(builders)} Residency — {locality}",
                            "transaction_type": txn,
                            "city": city,
                            "state": state,
                            "locality": locality,
                            "bhk": bhk,
                            "carpet_sqft": 520 + bhk * 360 + random.randint(-60, 180),
                            "monthly_rent_inr": rent if txn == "rent" else None,
                            "price_inr": price if txn == "buy" else None,
                            "deposit_inr": rent * (4 + variant) if txn == "rent" else None,
                            "amenities": random.sample(
                                ["parking", "gym", "pool", "power backup", "clubhouse", "garden", "lift"],
                                k=4,
                            ),
                            "rera_id": f"RERA/{state[:2].upper()}/{lid}",
                            "possession": random.choice(["Ready", "Dec 2026", "Mar 2027"]),
                        })
    offers = [
        {
            "listing_id": listings[i]["id"],
            "offer_inr": int((listings[i].get("price_inr") or 5000000) * 0.92),
            "valid_days": 14,
        }
        for i in range(0, min(200, len(listings)), 7)
    ]
    rera_records = [
        {
            "rera_id": L["rera_id"],
            "status": "Registered",
            "city": L["city"],
            "project": L["title"],
        }
        for L in listings[:400]
    ]
    return {
        "about": {"company": "UrbanNest Realty", "cities_served": len(CITIES)},
        "contact": {"phone": "+91-80-4000-1212", "email": "hello@urbannest.example"},
        "listings": listings,
        "localities": {
            f"{c} — {loc}": {
                "city": c,
                "vibe": random.choice(["family-friendly", "IT hub", "premium", "affordable"]),
                "avg_price_per_sqft_inr": random.randint(4500, 42000),
            }
            for c, _, _ in CITIES
            for loc in LOCALITIES[:6]
        },
        "loan_partners": [
            {"bank": b, "rate_pct": round(8.0 + i * 0.12, 2)}
            for i, b in enumerate(["HDFC", "SBI", "ICICI", "Axis", "Kotak", "PNB", "BoB", "IDFC"])
        ],
        "offers": offers,
        "rera_records": rera_records,
        "visit_slots": [
            {"city": c, "slot": f"{d} 10:00", "agent": f"Agent-{i}"}
            for i, (c, _, _) in enumerate(CITIES)
            for d in ("Sat", "Sun")
        ],
        "faqs": _faqs("re", ["Home loan", "RERA", "NRI buy", "Stamp duty", "Visit", "Rent agreement"], 10),
    }


# ---------------------------------------------------------------------------
# Restaurant
# ---------------------------------------------------------------------------
def gen_restaurant() -> dict[str, Any]:
    outlets, menu, reservations = [], [], []
    dishes = [
        "Smoked Aubergine Galouti", "Lamb Sukka", "Prawn Moilee", "Tandoori Platter",
        "Dal Makhani", "Biryani", "Sizzler", "Thali", "Sushi Platter", "Risotto",
    ]
    for i, (city, _, _) in enumerate(CITIES):
        for j, zone in enumerate(["Central", "Mall", "Airport", "Waterfront", "High Street"]):
            name = f"Saffron & Stone — {city} {zone}"
            outlets.append({
                "name": name,
                "city": city,
                "zone": zone,
                "address": f"Plot {100 + i + j}, {city}",
                "phone": f"+91-{20 + i}-{1000 + j}-{2000 + i}",
                "hours": "12:30–15:30, 19:00–23:30",
                "capacity": 50 + j * 20,
                "valet": j < 3,
                "dress_code": random.choice(["Smart casual", "Formal on Fri-Sat"]),
            })
            for dish in dishes:
                for v in range(2):
                    menu.append({
                        "outlet_city": city,
                        "outlet_zone": zone,
                        "name": dish,
                        "variant": v,
                        "diet": random.choice(["veg", "non-veg", "vegan", "seafood", "jain"]),
                        "price_inr": random.randint(280, 3200),
                        "spice_level": random.randint(0, 3),
                    })
    for r in range(350):
        reservations.append({
            "id": f"RES-{88000 + r}",
            "guest_name": f"Guest {r % 200}",
            "outlet_city": random.choice([c for c, _, _ in CITIES]),
            "party_size": random.randint(2, 14),
            "status": random.choice(["confirmed", "waitlist", "cancelled", "completed"]),
            "date_time": f"2026-06-{10 + r % 18:02d} 20:00",
        })
    return {
        "outlets": outlets,
        "menu": menu,
        "reservations": reservations,
        "private_rooms": [
            {"city": c, "name": f"Suite {i}", "max_pax": 8 + i * 4, "min_spend_inr": 25000 + i * 8000}
            for c, _, _ in CITIES
            for i in range(4)
        ],
        "catering_packages": [
            {"city": c, "package": p, "per_head_inr": random.randint(1200, 4500)}
            for c, _, _ in CITIES
            for p in ("Corporate lunch", "Wedding sangeet", "Birthday")
        ],
        "faqs": _faqs("rest", ["Reservation", "Allergies", "Parking", "Cancellation", "Private room"], 12),
        "policies": {"cancel_hours": 4, "hold_minutes": 15},
    }


# ---------------------------------------------------------------------------
# E-commerce
# ---------------------------------------------------------------------------
def gen_ecommerce() -> dict[str, Any]:
    orders, products, returns = [], [], []
    categories = ["Fashion", "Electronics", "Home", "Beauty", "Sports", "Books"]
    for i in range(450):
        oid = f"SS-{7800000 + i}"
        orders.append({
            "id": oid,
            "status": random.choice(
                ["Delivered", "Out for delivery", "Packed", "Cancelled", "RTO", "Delayed"]
            ),
            "city": random.choice([c for c, _, _ in CITIES]),
            "items": [{
                "sku": f"SKU-{i % 500}",
                "title": f"Item {i}",
                "price_inr": random.randint(299, 89999),
            }],
            "courier": random.choice(["Delhivery", "Bluedart", "Ecom Express", "DTDC"]),
            "eta_days": random.randint(1, 7),
        })
    for i in range(400):
        products.append({
            "sku": f"SKU-{i}",
            "title": f"{random.choice(categories)} product {i}",
            "category": random.choice(categories),
            "warranty": random.choice(["30 days", "1 year", "2 years", None]),
            "returnable": random.choice([True, True, False]),
            "price_inr": random.randint(199, 120000),
        })
    for i in range(220):
        returns.append({
            "id": f"RET-{i}",
            "order_id": f"SS-{7800000 + (i % 450)}",
            "reason": random.choice(["Size", "Defective", "Wrong item", "Changed mind"]),
            "status": random.choice(["Pickup scheduled", "Refunded", "Under review"]),
        })
    return {
        "orders": orders,
        "products": products,
        "returns": returns,
        "shipping_partners": [
            {"name": n, "sla_days": d} for n, d in [
                ("Delhivery", 3), ("Bluedart", 2), ("Ecom Express", 4), ("DTDC", 5),
            ]
        ],
        "faqs": _faqs("ecom", ["Tracking", "Refund", "Warranty", "Exchange", "COD"], 14),
        "return_policy": {"window_days": 14},
        "refund_policy": {"credit_days": 5, "bank_days": 7},
    }


# ---------------------------------------------------------------------------
# Recruitment
# ---------------------------------------------------------------------------
def gen_recruitment() -> dict[str, Any]:
    roles, screenings, interviews = [], [], []
    titles = [
        "Senior Backend Engineer", "Frontend Engineer", "DevOps Engineer",
        "Product Manager", "Customer Success Manager", "Data Analyst",
        "Sales Executive", "HR Business Partner", "QA Engineer", "Android Developer",
        "iOS Developer", "ML Engineer", "Technical Writer", "Finance Analyst",
    ]
    rid = 0
    for title in titles:
        for city, _, _ in CITIES:
            for mode in ("onsite", "hybrid", "remote"):
                rid += 1
                roles.append({
                    "id": f"TB-{rid:05d}",
                    "title": title,
                    "location": f"{city} ({mode})",
                    "city": city,
                    "experience_years": f"{2 + rid % 6}-{10 + rid % 5}",
                    "salary_band_inr_lpa": f"{10 + rid % 8}-{24 + rid % 10}",
                    "openings": random.randint(1, 8),
                    "skills": random.sample(
                        ["Python", "React", "AWS", "SQL", "Kubernetes", "Java", "Figma"],
                        k=3,
                    ),
                })
    for i in range(200):
        screenings.append({
            "candidate_ref": f"CAND-{i}",
            "role_id": f"TB-{(i % len(roles)) + 1:05d}",
            "score": random.randint(55, 95),
            "stage": random.choice(["L1 voice", "L2 tech", "L3 culture"]),
        })
    for i in range(150):
        interviews.append({
            "slot_id": f"INT-{i}",
            "role_id": roles[i % len(roles)]["id"],
            "datetime": f"2026-06-{12 + i % 15:02d} 11:00",
            "interviewer": f"Recruiter-{i % 20}",
        })
    return {
        "roles": roles,
        "screenings": screenings,
        "interviews": interviews,
        "benefits": ["Health insurance", "ESOPs", "Learning budget", "Hybrid work", "Parental leave"],
        "faqs": _faqs("rec", ["Salary", "Process", "Relocation", "Notice period", "Benefits"], 12),
        "company": {"name": "TalentBridge", "employees": 850, "offices": len(CITIES)},
    }


# ---------------------------------------------------------------------------
# Hotel
# ---------------------------------------------------------------------------
def gen_hotel() -> dict[str, Any]:
    properties, bookings, services = [], [], []
    room_types = ["Standard", "Deluxe", "Suite", "Villa", "Presidential"]
    for city, state, _ in CITIES:
        for room in room_types:
            for wing in ("Garden", "Lake", "City"):
                properties.append({
                    "id": f"tirtha-{city.lower()[:5]}-{room.lower()}-{wing.lower()}",
                    "name": f"Tirtha {city} — {room} ({wing})",
                    "city": city,
                    "state": state,
                    "room_type": room,
                    "wing": wing,
                    "per_night_inr": random.randint(3500, 120000),
                    "amenities": random.sample(
                        ["pool", "spa", "breakfast", "airport shuttle", "butler", "kids club"],
                        k=3,
                    ),
                })
    rates = [
        {
            "property_id": properties[i % len(properties)]["id"],
            "date": f"2026-06-{10 + i % 20:02d}",
            "rate_inr": random.randint(3000, 95000),
            "inventory": random.randint(1, 12),
        }
        for i in range(220)
    ]
    for b in range(420):
        bookings.append({
            "id": f"TIR-{9000 + b}",
            "property_city": random.choice([c for c, _, _ in CITIES]),
            "guest": f"Guest {b}",
            "status": random.choice(["confirmed", "checked-in", "cancelled"]),
            "check_in": f"2026-06-{10 + b % 18:02d}",
            "nights": random.randint(1, 7),
        })
    for s in range(320):
        services.append({
            "id": f"SRV-{s}",
            "type": random.choice(["housekeeping", "room service", "spa", "laundry", "maintenance"]),
            "sla_minutes": random.choice([15, 30, 45, 60]),
            "city": random.choice([c for c, _, _ in CITIES]),
        })
    return {
        "properties": properties,
        "rates": rates,
        "bookings": bookings,
        "services": services,
        "experiences": [
            {"city": c, "name": f"{exp} in {c}", "price_inr": random.randint(800, 12000)}
            for c, _, _ in CITIES
            for exp in ("City tour", "Heritage walk", "Cooking class", "Sunset cruise")
        ],
        "transport": [
            {"city": c, "route": "Airport pickup", "price_inr": random.randint(1200, 4500)}
            for c, _, _ in CITIES
        ],
        "faqs": _faqs("hotel", ["Check-in", "Cancellation", "Loyalty", "Pets", "Breakfast"], 12),
        "loyalty": {"name": "Tirtha Circle", "tiers": 4},
    }


# ---------------------------------------------------------------------------
# Banking
# ---------------------------------------------------------------------------
def gen_banking() -> dict[str, Any]:
    branches, atms, accounts, cards, loans, transactions, cheques = [], [], [], [], [], [], []
    for i, (city, state, prefix) in enumerate(CITIES):
        for b in range(8):
            code = f"{prefix}{random.randint(100000, 999999)}"
            branches.append({
                "city": city,
                "state": state,
                "name": f"Meridian {city} Branch {b + 1}",
                "ifsc": code,
                "hours": "9:30–17:30 weekdays",
                "services": random.sample(["loans", "forex", "locker", "demat"], k=2),
            })
        for a in range(22):
            atms.append({
                "atm_id": f"ATM-{city[:3]}-{i}-{a}",
                "city": city,
                "location": random.choice(LOCALITIES),
                "cash_available": random.choice([True, True, False]),
            })
    for i in range(280):
        last4 = f"{1000 + (i % 9000):04d}"
        accounts.append({
            "last4": last4,
            "type": random.choice(["Savings", "Current", "Salary", "NRI"]),
            "city": random.choice([c for c, _, _ in CITIES]),
            "balance_inr": round(random.uniform(5000, 8_000_000), 2),
            "status": random.choice(["active", "dormant", "frozen"]),
        })
    for i in range(200):
        cards.append({
            "last4": f"{2000 + (i % 8000):04d}",
            "network": random.choice(["Visa", "Mastercard", "RuPay"]),
            "type": random.choice(["Credit", "Debit", "Prepaid"]),
            "limit_inr": random.randint(25000, 1_500_000),
            "city": random.choice([c for c, _, _ in CITIES]),
        })
    for i in range(180):
        loans.append({
            "id": f"{'ML' if i % 2 else 'PL'}-{100000 + i}",
            "type": random.choice(["Home Loan", "Personal Loan", "Car Loan", "Education Loan"]),
            "emi_inr": random.randint(8000, 95000),
            "outstanding_inr": random.randint(100000, 6_000_000),
            "city": random.choice([c for c, _, _ in CITIES]),
        })
    for i in range(320):
        transactions.append({
            "ref": f"TXN{9900000 + i}",
            "account_last4": f"{1000 + (i % 200):04d}",
            "amount_inr": random.randint(-250000, 350000),
            "desc": random.choice(["UPI", "NEFT", "Salary", "ATM", "POS", "IMPS"]),
            "date": f"2026-05-{1 + i % 28:02d}",
        })
    for i in range(120):
        cheques.append({
            "cheque_no": f"CHQ-{i}",
            "account_last4": f"{3000 + (i % 500):04d}",
            "status": random.choice(["cleared", "pending", "bounced", "stopped"]),
            "amount_inr": random.randint(5000, 500000),
        })
    investments = [
        {"scheme": s, "min_inr": m, "risk": r}
        for s, m, r in [
            ("FD 1Y", 10000, "low"),
            ("RD", 500, "low"),
            ("Equity MF", 500, "high"),
            ("Debt MF", 1000, "medium"),
            ("PPF", 500, "low"),
        ]
    ]
    fraud_cases = [
        {"id": f"FR-{i}", "type": t, "action": "block card and file FIR guidance"}
        for i, t in enumerate(["Phishing SMS", "UPI scam", "Skimming", "Identity theft"] * 15)
    ]
    return {
        "about": {"bank": "Meridian Bank", "branches": len(branches), "atms": len(atms)},
        "branches": branches,
        "atms": atms,
        "accounts": accounts,
        "cards": cards,
        "loans": loans,
        "transactions": transactions,
        "cheques": cheques,
        "investments": investments,
        "fraud_cases": fraud_cases,
        "fees": {"atm_other_bank_inr": 21, "rtgs_inr": 25},
        "dispute_policy": {"raise_within_days": 60, "investigation_days": 30},
        "policies": {"card_block_immediate": True, "replacement_days": "5-7"},
        "faqs": _faqs("bank", ["Balance", "Card block", "EMI", "IFSC", "FD", "Fraud"], 14),
    }


# ---------------------------------------------------------------------------
# Debt collection
# ---------------------------------------------------------------------------
def gen_debt_collection() -> dict[str, Any]:
    accounts, payment_plans, callbacks, settlements = [], [], [], []
    for i in range(520):
        accounts.append({
            "id": f"ACC-{10000 + i}",
            "city": random.choice([c for c, _, _ in CITIES]),
            "overdue_days": random.randint(5, 180),
            "outstanding_inr": random.randint(3000, 750000),
            "type": random.choice(["Credit Card", "Personal Loan", "Home Loan EMI", "BNPL", "Overdraft"]),
            "bucket": random.choice(["soft", "medium", "hard", "legal"]),
            "last_contact": f"2026-05-{1 + i % 28:02d}",
        })
    for i in range(120):
        payment_plans.append({
            "id": f"P{i}",
            "account_id": f"ACC-{10000 + (i % 420)}",
            "months": 3 + i % 12,
            "discount_pct": i % 15,
            "min_payment_inr": random.randint(2000, 50000),
        })
    for i in range(280):
        callbacks.append({
            "id": f"CB-{i}",
            "account_id": f"ACC-{10000 + (i % 420)}",
            "scheduled": f"2026-06-{10 + i % 18:02d} 14:00",
            "agent": f"Agent-{i % 30}",
        })
    for i in range(150):
        settlements.append({
            "id": f"SET-{i}",
            "account_id": f"ACC-{10000 + (i % 420)}",
            "lump_sum_inr": random.randint(10000, 200000),
            "valid_until": "2026-06-30",
        })
    return {
        "accounts": accounts,
        "payment_plans": payment_plans,
        "callbacks": callbacks,
        "settlements": settlements,
        "compliance": {
            "calling_window": "08:00-19:00",
            "max_calls_per_day": 2,
            "dnc_honour_hours": 72,
        },
        "dispute_routing": [{"reason": r, "escalate": "compliance@avenir.example"} for r in (
            "Already paid", "Wrong person", "Fraud", "Hardship",
        )],
        "faqs": _faqs("debt", ["Payment plan", "Settlement", "Dispute", "DNC", "Legal"], 12),
    }


# ---------------------------------------------------------------------------
# Travel
# ---------------------------------------------------------------------------
def gen_travel() -> dict[str, Any]:
    flights, hotels, bookings, visas = [], [], [], []
    airlines = ["IndiGo", "Air India", "Vistara", "SpiceJet", "Emirates", "Singapore Airlines", "Qatar"]
    for i in range(520):
        o, d = random.choice(AIRPORTS), random.choice(AIRPORTS)
        if o == d:
            continue
        flights.append({
            "from": o,
            "to": d,
            "airline": random.choice(airlines),
            "fare_inr": random.randint(2500, 125000),
            "stops": random.randint(0, 2),
            "class": random.choice(["Economy", "Premium Economy", "Business"]),
            "flight_no": f"{random.choice(['6E', 'AI', 'UK'])}{random.randint(100, 9999)}",
        })
    for dest in [c for c, _, _ in CITIES] + ["Bali", "Dubai", "Singapore", "London", "Tokyo"]:
        for j in range(8):
            hotels.append({
                "city": dest,
                "name": f"Stay {dest} {j}",
                "stars": random.randint(3, 5),
                "per_night_inr": random.randint(2500, 85000),
            })
    for i in range(200):
        bookings.append({
            "id": f"WB-{20000 + i}",
            "type": random.choice(["flight", "hotel", "package"]),
            "status": random.choice(["confirmed", "cancelled", "pending"]),
            "from": random.choice(AIRPORTS),
            "to": random.choice(AIRPORTS),
        })
    for country in ["Thailand", "UAE", "UK", "USA", "Japan", "France", "Australia", "Malaysia"]:
        for i in range(12):
            visas.append({
                "country": country,
                "type": random.choice(["Tourist", "Business", "Student"]),
                "processing_days": random.randint(3, 21),
                "fee_inr": random.randint(3000, 25000),
            })
    return {
        "flights": flights,
        "hotels": hotels,
        "bookings": bookings,
        "visas": visas,
        "destinations": {
            c: {"best_months": ["Oct", "Nov", "Dec"], "avg_temp_c": random.randint(18, 34)}
            for c, _, _ in CITIES
        },
        "experiences": [
            {"dest": d, "name": f"Tour {d}", "price_inr": random.randint(1500, 25000)}
            for d in ["Bali", "Dubai", "Goa", "Kerala", "Rajasthan"]
            for _ in range(20)
        ],
        "policies": {"cancel_fee_pct": 15, "change_fee_inr": 2500},
        "disruption_sla": {"rebook_within_hours": 6, "refund_days": 7},
        "faqs": _faqs("travel", ["Visa", "Baggage", "Cancellation", "Insurance", "Multi-city"], 12),
    }


# ---------------------------------------------------------------------------
# College LDCE
# ---------------------------------------------------------------------------
def gen_college_ldce() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "college" / "data" / "ldce.json"
    base: dict[str, Any] = {}
    if path.exists():
        base = json.loads(path.read_text(encoding="utf-8"))
        base.pop("id", None)

    programs, cutoffs, scholarships, events, faculty, alumni, outreach = [], [], [], [], [], [], []
    for branch in BRANCHES_ENG:
        for level in ("UG", "PG", "Diploma"):
            for quota in ("General", "OBC", "SC", "ST", "EWS"):
                programs.append({
                    "branch": branch,
                    "level": level,
                    "quota": quota,
                    "city": "Ahmedabad",
                    "intake": random.randint(30, 120),
                    "duration_years": 4 if level == "UG" else 2,
                })
    for year in range(2018, 2027):
        for branch in BRANCHES_ENG[:6]:
            cutoffs.append({
                "year": year,
                "branch": branch,
                "percentile": round(random.uniform(70, 99.5), 2),
                "category": random.choice(["General", "OBC", "SC"]),
            })
    for i in range(180):
        scholarships.append({
            "id": f"SCH-{i}",
            "name": f"Merit / Need scheme {i % 25}",
            "amount_inr": random.randint(10000, 150000),
            "eligibility": random.choice([">8 CGPA", "Family income", "Sports", "Girl child"]),
        })
    for i in range(160):
        events.append({
            "id": f"EVT-{i}",
            "title": random.choice(["Techfest", "Cultural", "Sports", "Guest lecture", "Workshop"]),
            "date": f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "venue": random.choice(["Main auditorium", "Seminar hall", "Ground"]),
        })
    for i in range(200):
        faculty.append({
            "id": f"FAC-{i}",
            "dept": random.choice(BRANCHES_ENG),
            "designation": random.choice(["Professor", "Associate Prof", "Assistant Prof"]),
            "research_area": random.choice(["AI", "Structures", "VLSI", "Thermodynamics", "Networks"]),
        })
    for i in range(150):
        alumni.append({
            "batch": 2000 + (i % 25),
            "company": random.choice(["Google", "TCS", "Amazon", "Startups", "PSU", "MS abroad"]),
            "branch": random.choice(BRANCHES_ENG),
            "role": random.choice(["SWE", "Analyst", "Founder", "Researcher"]),
        })
    for city in [c for c, _, _ in CITIES[:12]]:
        for session in ("June", "December"):
            outreach.append({
                "city": city,
                "session": session,
                "mode": random.choice(["In-person", "Webinar", "Hybrid"]),
                "contact": f"outreach+{city[:3].lower()}@ldce.ac.in",
            })

    faqs = _faqs("ldce", [
        "ACPC", "Hostel", "Placement", "Fees", "Scholarship", "Campus", "GTU", "Internship",
    ], 18)

    merged = {
        **{k: v for k, v in base.items() if k not in ("meta",)},
        "programs_expanded": programs,
        "cutoffs": cutoffs,
        "scholarships": scholarships,
        "events": events,
        "faculty": faculty,
        "alumni": alumni,
        "outreach_sessions": outreach,
        "city_guides": {
            c: {"note": f"Counselling support — {c}"}
            for c, _, _ in CITIES[:15]
        },
        "faqs": faqs,
    }
    return merged


def main() -> None:
    gens = {
        "real_estate": gen_real_estate,
        "restaurant": gen_restaurant,
        "ecommerce": gen_ecommerce,
        "recruitment": gen_recruitment,
        "hotel": gen_hotel,
        "banking": gen_banking,
        "debt_collection": gen_debt_collection,
        "travel": gen_travel,
        "college_ldce": gen_college_ldce,
    }
    print(f"Generating knowledge bases (target ≥ {MIN_RECORDS:,} records each)...\n")
    total = 0
    for name, fn in gens.items():
        total += _write(name, fn())
    print(f"\nTotal records across all domains: {total:,}")


if __name__ == "__main__":
    main()
