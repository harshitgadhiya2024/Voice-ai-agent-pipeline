"""Legacy slot questions kept for backward compat. New code reads slots
directly from each UseCase definition (use_cases/*.py)."""
from __future__ import annotations

# Kept only so any older import doesn't break — nothing reads this anymore.
SLOT_QUESTIONS: dict[str, str] = {}
AGENT_REQUIRED_SLOTS: dict[str, list[str]] = {}
AGENT_IDS: tuple[str, ...] = ()
