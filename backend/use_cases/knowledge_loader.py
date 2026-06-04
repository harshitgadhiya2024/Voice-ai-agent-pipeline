"""Load and query large JSON knowledge bases per use case."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent / "data"

_MAX_LISTINGS = 12
_MAX_FAQS = 15
_MAX_LOCATIONS = 8
_MAX_ORDERS = 5
_MAX_GENERIC_LIST = 15
_MAX_JSON_CHARS = 28_000


@lru_cache(maxsize=32)
def load_knowledge(use_case_id: str) -> dict[str, Any]:
    path = _DATA_DIR / f"{use_case_id}.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def count_knowledge_records(knowledge: dict[str, Any]) -> int:
    """Count discrete records; prefer meta.record_count when present."""
    meta = knowledge.get("meta", {})
    if isinstance(meta, dict) and meta.get("record_count"):
        return int(meta["record_count"])
    total = 0
    for key, val in knowledge.items():
        if key == "meta":
            continue
        if isinstance(val, list):
            total += len(val)
        elif isinstance(val, dict):
            for sub_v in val.values():
                if isinstance(sub_v, list):
                    total += len(sub_v)
                elif isinstance(sub_v, dict):
                    total += len(sub_v)
    return total


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def _last4(slots: dict[str, Any], *keys: str) -> str:
    for k in keys:
        raw = str(slots.get(k, "") or "")
        if raw:
            digits = re.sub(r"\D", "", raw)
            if len(digits) >= 4:
                return digits[-4:]
    return ""


def _filter_listings(
    listings: list[dict],
    slots: dict[str, Any],
    limit: int = _MAX_LISTINGS,
) -> list[dict]:
    if not listings:
        return []
    loc = _norm(str(slots.get("location", "") or slots.get("city", "")))
    txn = _norm(str(slots.get("transaction_type", "")))
    bhk = slots.get("bhk")
    out = listings
    if loc:
        out = [
            x
            for x in out
            if loc in _norm(x.get("locality", ""))
            or loc in _norm(x.get("city", ""))
            or loc in _norm(x.get("title", ""))
        ] or out
    if txn:
        out = [x for x in out if txn in _norm(x.get("transaction_type", ""))] or out
    if bhk:
        try:
            b = int(bhk)
            out = [x for x in out if x.get("bhk") == b] or out
        except (TypeError, ValueError):
            pass
    listing_id = _norm(str(slots.get("listing_id", "")))
    if listing_id:
        matched = [x for x in out if listing_id in _norm(x.get("id", ""))]
        out = matched or out
    return out[:limit]


def _filter_by_key(
    items: list[dict],
    slot_key: str,
    field: str,
    slots: dict[str, Any],
    limit: int = _MAX_GENERIC_LIST,
) -> list[dict]:
    needle = _norm(str(slots.get(slot_key, "")))
    if not needle or not items:
        return items[:limit]
    matched = [x for x in items if needle in _norm(str(x.get(field, "")))]
    return (matched or items)[:limit]


def _filter_by_id_prefix(
    items: list[dict],
    slot_key: str,
    id_field: str,
    slots: dict[str, Any],
    limit: int = _MAX_GENERIC_LIST,
) -> list[dict]:
    needle = _norm(str(slots.get(slot_key, "")))
    if not needle:
        return items[:limit]
    matched = [x for x in items if needle in _norm(str(x.get(id_field, "")))]
    return (matched or items)[:limit]


def build_context_for_intent(
    knowledge: dict[str, Any],
    intent_id: str,
    knowledge_keys: tuple[str, ...],
    slots: dict[str, Any] | None = None,
) -> str:
    """
    Agentic context assembly: pick relevant slices from 1000+ records
    using intent + filled slots (location, order id, account last4, etc.).
    """
    slots = slots or {}
    sections: dict[str, Any] = {}

    for key in knowledge_keys or tuple(knowledge.keys()):
        if key not in knowledge:
            continue
        val = knowledge[key]

        if key in ("listings", "properties") and isinstance(val, list):
            sections[key] = _filter_listings(val, slots)
        elif key == "hotels" and isinstance(val, list):
            sections[key] = _filter_by_key(val, "destination", "city", slots)
        elif key == "flights" and isinstance(val, list):
            origin = _norm(str(slots.get("origin", "")))
            dest = _norm(str(slots.get("destination", "")))
            fl = val
            if origin:
                fl = [x for x in fl if origin in _norm(x.get("from", ""))] or fl
            if dest:
                fl = [x for x in fl if dest in _norm(x.get("to", ""))] or fl
            sections[key] = fl[:_MAX_LISTINGS]
        elif key == "orders" and isinstance(val, list):
            oid = _norm(str(slots.get("order_id", "")))
            if oid:
                matched = [x for x in val if oid in _norm(x.get("id", ""))]
                sections[key] = matched[:_MAX_ORDERS] or val[:_MAX_ORDERS]
            else:
                sections[key] = val[:_MAX_ORDERS]
        elif key == "returns" and isinstance(val, list):
            oid = _norm(str(slots.get("order_id", "")))
            if oid:
                matched = [x for x in val if oid in _norm(x.get("order_id", ""))]
                sections[key] = matched[:_MAX_ORDERS] or val[:5]
            else:
                sections[key] = val[:5]
        elif key == "accounts" and isinstance(val, list):
            last4 = _last4(slots, "account_last4", "account_id")
            if last4:
                matched = [x for x in val if str(x.get("last4", "")) == last4]
                sections[key] = matched or val[:3]
            else:
                city = _norm(str(slots.get("city", "")))
                if city:
                    matched = [x for x in val if city in _norm(x.get("city", ""))]
                    sections[key] = (matched or val)[:_MAX_GENERIC_LIST]
                else:
                    sections[key] = val[:3]
        elif key == "cards" and isinstance(val, list):
            last4 = _last4(slots, "card_last4")
            if last4:
                matched = [x for x in val if str(x.get("last4", "")) == last4]
                sections[key] = matched or val[:3]
            else:
                sections[key] = val[:5]
        elif key == "loans" and isinstance(val, list):
            sections[key] = _filter_by_id_prefix(val, "loan_id", "id", slots, 5)
        elif key == "transactions" and isinstance(val, list):
            last4 = _last4(slots, "account_last4")
            if last4:
                matched = [x for x in val if str(x.get("account_last4", "")) == last4]
                sections[key] = matched[:8] or val[:5]
            else:
                sections[key] = val[:5]
        elif key == "cheques" and isinstance(val, list):
            last4 = _last4(slots, "account_last4")
            if last4:
                matched = [x for x in val if str(x.get("account_last4", "")) == last4]
                sections[key] = matched[:5] or val[:3]
            else:
                sections[key] = val[:3]
        elif key == "branches" and isinstance(val, list):
            sections[key] = _filter_by_key(val, "city", "city", slots, 8)
        elif key == "atms" and isinstance(val, list):
            sections[key] = _filter_by_key(val, "city", "city", slots, 8)
        elif key in ("roles", "programs_expanded", "cutoffs") and isinstance(val, list):
            loc = _norm(str(slots.get("location", "") or slots.get("city", "")))
            branch = _norm(str(slots.get("branch", "") or slots.get("role_id", "")))
            out = val
            if loc:
                out = [x for x in out if loc in _norm(x.get("location", "")) or loc in _norm(x.get("city", ""))] or out
            if branch:
                out = [x for x in out if branch in _norm(x.get("branch", "")) or branch in _norm(x.get("title", "")) or branch in _norm(x.get("id", ""))] or out
            sections[key] = out[:_MAX_GENERIC_LIST]
        elif key == "menu" and isinstance(val, list):
            city = _norm(str(slots.get("outlet", "") or slots.get("city", "")))
            if city:
                sections[key] = [x for x in val if city in _norm(x.get("outlet_city", ""))][:12] or val[:8]
            else:
                sections[key] = val[:8]
        elif key == "outlets" and isinstance(val, list):
            outlet = _norm(str(slots.get("outlet", "") or slots.get("city", "")))
            if outlet:
                sections[key] = [x for x in val if outlet in _norm(x.get("name", "")) or outlet in _norm(x.get("city", ""))] or val[:6]
            else:
                sections[key] = val[:6]
        elif key == "reservations" and isinstance(val, list):
            name = _norm(str(slots.get("guest_name", "")))
            if name:
                sections[key] = [x for x in val if name in _norm(x.get("guest_name", ""))][:5] or val[:3]
            else:
                sections[key] = val[:3]
        elif key in ("bookings",) and isinstance(val, list):
            bid = _norm(str(slots.get("booking_id", "")))
            if bid:
                sections[key] = [x for x in val if bid in _norm(x.get("id", ""))][:3] or val[:3]
            else:
                sections[key] = val[:3]
        elif key == "rates" and isinstance(val, list):
            prop = _norm(str(slots.get("property", "")))
            if prop:
                sections[key] = [x for x in val if prop in _norm(x.get("property_id", ""))][:8] or val[:5]
            else:
                sections[key] = val[:5]
        elif key in (
            "payment_plans", "callbacks", "settlements", "screenings", "interviews",
            "offers", "rera_records", "fraud_cases", "investments", "visas",
            "scholarships", "events", "faculty", "alumni", "outreach_sessions",
            "products", "private_rooms", "catering_packages", "experiences", "transport",
        ) and isinstance(val, list):
            if intent_id and len(val) > _MAX_GENERIC_LIST:
                sections[key] = val[:_MAX_GENERIC_LIST]
            else:
                sections[key] = val[:_MAX_GENERIC_LIST]
        elif key == "localities" and isinstance(val, dict):
            loc = _norm(str(slots.get("location", "")))
            if loc:
                picked = {k: v for k, v in val.items() if loc in _norm(k)}
                sections[key] = picked or dict(list(val.items())[:_MAX_LOCATIONS])
            else:
                sections[key] = dict(list(val.items())[:_MAX_LOCATIONS])
        elif key == "faqs" and isinstance(val, list):
            topic = _norm(str(slots.get("topic", "")))
            if topic:
                matched = [x for x in val if topic in _norm(x.get("topic", "")) or topic in _norm(x.get("q", ""))]
                sections[key] = matched[:_MAX_FAQS] or val[:_MAX_FAQS]
            else:
                sections[key] = val[:_MAX_FAQS]
        elif isinstance(val, list) and len(val) > 20:
            sections[key] = val[:_MAX_GENERIC_LIST]
        else:
            sections[key] = val

    if not sections:
        sections = {k: knowledge[k] for k in list(knowledge.keys())[:8] if k != "meta"}

    text = json.dumps(sections, ensure_ascii=False, indent=2)
    if len(text) > _MAX_JSON_CHARS:
        text = text[:_MAX_JSON_CHARS] + "\n... (truncated; full catalog has 1000+ records)"
    return text
