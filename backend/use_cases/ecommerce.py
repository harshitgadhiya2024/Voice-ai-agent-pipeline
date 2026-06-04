"""E-commerce Customer Support Voice AI Agent — orders, returns, refunds."""
from __future__ import annotations

from use_cases.base import IntentSpec, SlotSpec, UseCase


ECOMMERCE = UseCase(
    id="ecommerce",
    name="E-commerce Support",
    company="ShopSphere",
    tagline="Track orders, start returns, get answers in seconds",
    description=(
        "A 24x7 e-commerce support agent that handles order tracking, returns, "
        "refunds, exchanges, and product questions — deflecting 80% of L1 "
        "tickets without a human handoff."
    ),
    icon="shopping-bag",
    accent="indigo",
    persona_name_female="Riya",
    persona_name_male="Karan",
    default_voice_gender="female",
    greeting=(
        "Hi, this is Riya from ShopSphere support. I can track your order, "
        "start a return, or help with a product question — what do you need?"
    ),
    sample_questions=(
        "Where is my order SS-7821941?",
        "I want to return the running shoes I ordered last week",
        "My package was delivered but I didn't receive it",
        "How long does a refund take after pickup?",
        "Can I change the delivery address for order SS-7822055?",
    ),
    persona=(
        "You are a calm, empathetic e-commerce support agent. Apologize "
        "naturally for any inconvenience, look up the order, and resolve in "
        "the call when possible. Escalate only when policy actually requires "
        "human review (e.g., damaged item complaints with photos)."
    ),
    fallback_disclaimer=(
        "Demo data — real orders are looked up via your shop's order API."
    ),
    intents=(
        IntentSpec(
            id="track_order",
            label="Order tracking",
            description="Where is my package, ETA, courier info.",
            required_slots=("order_id",),
            knowledge_keys=("orders", "shipping_partners"),
        ),
        IntentSpec(
            id="start_return",
            label="Returns / exchange",
            description="Initiate a return or exchange.",
            required_slots=("order_id", "return_reason"),
            knowledge_keys=("return_policy", "orders"),
        ),
        IntentSpec(
            id="refund_status",
            label="Refund status",
            description="Where is my refund / how long will it take.",
            required_slots=("order_id",),
            knowledge_keys=("refund_policy", "orders"),
        ),
        IntentSpec(
            id="modify_order",
            label="Modify order",
            description="Change address, cancel, change size.",
            required_slots=("order_id",),
            knowledge_keys=("modification_policy", "orders"),
        ),
        IntentSpec(
            id="product_qa",
            label="Product question",
            description="Specs, compatibility, warranty.",
            knowledge_keys=("products", "warranty_policy"),
        ),
        IntentSpec(
            id="return_status",
            label="Return status",
            description="Track pickup, refund, or exchange progress.",
            required_slots=("order_id",),
            knowledge_keys=("returns", "refund_policy"),
        ),
        IntentSpec(
            id="delivery_issue",
            label="Delivery problem",
            description="Delayed, RTO, or not received packages.",
            required_slots=("order_id",),
            knowledge_keys=("orders", "shipping_partners"),
        ),
        IntentSpec(
            id="general",
            label="General",
            description="Account, payment options, contact, FAQs.",
            knowledge_keys=("about", "faqs"),
        ),
    ),
    slots={
        "order_id": SlotSpec(
            id="order_id",
            question="Could you share your order ID — it usually starts with SS-?",
        ),
        "return_reason": SlotSpec(
            id="return_reason",
            question="What is the reason for the return — wrong size, "
            "damaged, didn't like, or something else?",
        ),
        "delivery_address": SlotSpec(
            id="delivery_address",
            question="What is the new delivery address you'd like to use?",
        ),
    },
    knowledge={
        "about": {
            "company": "ShopSphere",
            "founded": 2018,
            "categories": ["Fashion", "Electronics", "Home", "Beauty"],
            "delivery_to": ["India", "UAE", "Singapore"],
        },
        "payment_methods": [
            "Credit/Debit Card",
            "UPI",
            "Net Banking",
            "Cash on Delivery (orders below ₹15,000)",
            "ShopSphere Wallet",
            "EMI (3/6/9/12 months on cards >₹3000)",
        ],
        "orders": [
            {
                "id": "SS-7821941",
                "customer": "Anita Sharma",
                "items": [
                    {"sku": "NK-AIR-001", "title": "Nike Pegasus 41", "qty": 1, "price_inr": 9999}
                ],
                "status": "Out for delivery",
                "courier": "Delhivery",
                "tracking_url": "https://track.delhivery.example/SS-7821941",
                "ordered_on": "2026-05-30",
                "expected_delivery": "2026-06-04",
            },
            {
                "id": "SS-7822055",
                "customer": "Rahul Mehta",
                "items": [
                    {"sku": "ASUS-X13", "title": "ASUS ROG Flow X13", "qty": 1, "price_inr": 134999}
                ],
                "status": "Packed at warehouse",
                "courier": "Bluedart",
                "ordered_on": "2026-06-02",
                "expected_delivery": "2026-06-06",
            },
            {
                "id": "SS-7820005",
                "customer": "Priya Patel",
                "items": [
                    {"sku": "ZARA-DR-22", "title": "Zara Linen Dress", "qty": 1, "price_inr": 4490}
                ],
                "status": "Delivered",
                "courier": "Ecom Express",
                "ordered_on": "2026-05-22",
                "delivered_on": "2026-05-25",
                "return_window_ends": "2026-06-08",
            },
        ],
        "shipping_partners": [
            {"name": "Delhivery", "avg_days": 3, "tracking_sla_hours": 6},
            {"name": "Bluedart", "avg_days": 2, "tracking_sla_hours": 4},
            {"name": "Ecom Express", "avg_days": 4, "tracking_sla_hours": 8},
        ],
        "return_policy": {
            "window_days": 14,
            "categories_excluded": ["Innerwear", "Beauty (opened)", "Customized"],
            "pickup_free": True,
            "tags_required": True,
        },
        "refund_policy": {
            "after_pickup_days": "5-7 business days",
            "to_original_payment": True,
            "store_credit_option": True,
            "store_credit_bonus_pct": 5,
        },
        "modification_policy": {
            "address_change_until": "Before shipping",
            "free_cancel_until": "Before shipping",
            "size_change": "Cancel + reorder; price-locked for 24h",
        },
        "warranty_policy": {
            "electronics_default_years": 1,
            "extended_available": True,
            "manufacturer_handled": ["Apple", "Samsung", "Sony"],
        },
        "products": [
            {"sku": "NK-AIR-001", "title": "Nike Pegasus 41", "category": "Footwear", "warranty": "30 days"},
            {"sku": "ASUS-X13", "title": "ASUS ROG Flow X13", "category": "Laptop", "warranty": "2 years"},
            {"sku": "ZARA-DR-22", "title": "Zara Linen Dress", "category": "Apparel", "warranty": None},
        ],
    },
)
