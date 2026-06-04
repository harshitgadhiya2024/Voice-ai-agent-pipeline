"""Load and query LDCE college knowledge for agent context."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent / "data"


@lru_cache(maxsize=4)
def load_college(college_id: str = "ldce") -> dict[str, Any]:
    path = _DATA_DIR / f"{college_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"College knowledge not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def college_summary(college_id: str = "ldce") -> str:
    """Short institute overview for all agents."""
    c = load_college(college_id)
    return (
        f"{c['name']} ({c['short_name']}), {c['address']}. "
        f"Affiliated to {c['affiliation']}. Website: {c['website']}. "
        f"{c['about']}"
    )


def context_for_agent(agent_id: str, college_id: str = "ldce") -> str:
    """Return focused knowledge snippet for a specialist agent."""
    c = load_college(college_id)
    sections: dict[str, str] = {
        "general": (
            f"Overview: {c['about']}\n"
            f"Motto: {c['motto']}\n"
            f"Stats: {json.dumps(c.get('stats', {}), ensure_ascii=False)}\n"
            f"Quick links: {', '.join(c.get('quick_links', []))}\n"
            f"Contact: {json.dumps(c.get('contact', {}), ensure_ascii=False)}"
        ),
        "courses": (
            f"UG departments ({len(c['ug_departments'])}): "
            f"{', '.join(c['ug_departments'])}.\n"
            f"PG programs: {', '.join(c['pg_programs'])}."
        ),
        "admissions": json.dumps(c.get("admissions", {}), ensure_ascii=False),
        "fees": json.dumps(c.get("fees", {}), ensure_ascii=False),
        "placement": json.dumps(c.get("placement", {}), ensure_ascii=False),
        "hostel": json.dumps(
            {"hostel": c["facilities"].get("hostel"), "campus": c["facilities"]},
            ensure_ascii=False,
        ),
        "facilities": json.dumps(c.get("facilities", {}), ensure_ascii=False),
        "innovation": json.dumps(c.get("innovation", {}), ensure_ascii=False),
    }
    return sections.get(agent_id, sections["general"])
