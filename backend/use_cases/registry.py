"""Use-case registry — single source of truth for all demos."""
from __future__ import annotations

from dataclasses import replace

from use_cases.base import UseCase
from use_cases.knowledge_loader import load_knowledge
from use_cases.real_estate import REAL_ESTATE
from use_cases.restaurant import RESTAURANT
from use_cases.ecommerce import ECOMMERCE
from use_cases.recruitment import RECRUITMENT
from use_cases.hotel import HOTEL
from use_cases.banking import BANKING
from use_cases.debt_collection import DEBT_COLLECTION
from use_cases.travel import TRAVEL
from use_cases.college_ldce import LDCE_COLLEGE

_RAW: tuple[UseCase, ...] = (
    REAL_ESTATE,
    RESTAURANT,
    ECOMMERCE,
    RECRUITMENT,
    HOTEL,
    BANKING,
    DEBT_COLLECTION,
    TRAVEL,
    LDCE_COLLEGE,
)

_RAW_BY_ID: dict[str, UseCase] = {uc.id: uc for uc in _RAW}

# Hydrated use cases (with JSON knowledge) — loaded on first request, not at import.
_USE_CASE_CACHE: dict[str, UseCase] = {}


def _hydrate(uc: UseCase) -> UseCase:
    """Attach large JSON knowledge base (1000+ records total) per domain."""
    kb = load_knowledge(uc.id)
    if kb:
        return replace(uc, knowledge=kb)
    return uc


# First demo selected on the gallery if user hits the demo route directly.
DEFAULT_USE_CASE_ID = "real_estate"


def get_use_case(use_case_id: str) -> UseCase:
    uid = use_case_id if use_case_id in _RAW_BY_ID else DEFAULT_USE_CASE_ID
    if uid not in _USE_CASE_CACHE:
        _USE_CASE_CACHE[uid] = _hydrate(_RAW_BY_ID[uid])
    return _USE_CASE_CACHE[uid]


def list_use_cases() -> list[dict]:
    return [uc.to_metadata() for uc in _RAW]


def all_use_case_ids() -> tuple[str, ...]:
    return tuple(_RAW_BY_ID.keys())


# Back-compat for code that imported USE_CASES (lazy dict view).
class _UseCasesProxy(dict):
    def __getitem__(self, key: str) -> UseCase:
        return get_use_case(key)

    def get(self, key: str, default=None):  # type: ignore[override]
        if key not in _RAW_BY_ID:
            return default
        return get_use_case(key)

    def values(self):
        return [get_use_case(uid) for uid in _RAW_BY_ID]

    def items(self):
        return [(uid, get_use_case(uid)) for uid in _RAW_BY_ID]

    def __iter__(self):
        return iter(_RAW_BY_ID)

    def __len__(self) -> int:
        return len(_RAW_BY_ID)


USE_CASES: _UseCasesProxy = _UseCasesProxy()
