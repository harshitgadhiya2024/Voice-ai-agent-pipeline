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


def _hydrate(uc: UseCase) -> UseCase:
    """Attach large JSON knowledge base (1000+ records total) per domain."""
    kb = load_knowledge(uc.id)
    if kb:
        return replace(uc, knowledge=kb)
    return uc


USE_CASES: dict[str, UseCase] = {uc.id: _hydrate(uc) for uc in _RAW}

# First demo selected on the gallery if user hits the demo route directly.
DEFAULT_USE_CASE_ID = "real_estate"


def get_use_case(use_case_id: str) -> UseCase:
    return USE_CASES.get(use_case_id) or USE_CASES[DEFAULT_USE_CASE_ID]


def list_use_cases() -> list[dict]:
    return [uc.to_metadata() for uc in USE_CASES.values()]
