"""UseCase, Intent, and Slot specifications for demo Voice AI agents."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SlotSpec:
    """A piece of structured info the agent needs to collect from the user."""

    id: str
    question: str
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntentSpec:
    """One specialist intent inside a use case (mapped to a graph node)."""

    id: str
    label: str
    description: str
    required_slots: tuple[str, ...] = ()
    knowledge_keys: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class UseCase:
    """A complete demo Voice AI agent definition."""

    id: str
    name: str
    company: str
    tagline: str
    description: str
    icon: str
    accent: str
    persona_name_female: str
    persona_name_male: str
    greeting: str
    sample_questions: tuple[str, ...]
    persona: str
    fallback_disclaimer: str
    intents: tuple[IntentSpec, ...]
    slots: dict[str, SlotSpec]
    knowledge: dict[str, Any] = field(default_factory=dict)
    default_voice_gender: str = "female"

    @property
    def intent_ids(self) -> tuple[str, ...]:
        return tuple(i.id for i in self.intents)

    def find_intent(self, intent_id: str) -> IntentSpec:
        for i in self.intents:
            if i.id == intent_id:
                return i
        return self.intents[0]

    def required_slots(self, intent_id: str) -> tuple[str, ...]:
        return self.find_intent(intent_id).required_slots

    def slot_question(self, slot_id: str) -> str:
        spec = self.slots.get(slot_id)
        if spec is None:
            return f"Could you share more details about {slot_id.replace('_', ' ')}?"
        return spec.question

    def context_for_intent(
        self, intent_id: str, slots: dict[str, Any] | None = None
    ) -> str:
        """Agentic retrieval: filter 1000+ records by intent + collected slots."""
        from use_cases.knowledge_loader import build_context_for_intent

        intent = self.find_intent(intent_id)
        keys = intent.knowledge_keys or tuple(self.knowledge.keys())
        return build_context_for_intent(
            self.knowledge, intent_id, keys, slots or {}
        )

    @property
    def knowledge_record_count(self) -> int:
        from use_cases.knowledge_loader import (
            count_knowledge_records,
            load_knowledge,
        )

        if self.knowledge:
            return count_knowledge_records(self.knowledge)
        return count_knowledge_records(load_knowledge(self.id))

    def to_metadata(self) -> dict[str, Any]:
        """Public metadata for the frontend gallery (no full knowledge dump)."""
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
            "tagline": self.tagline,
            "description": self.description,
            "icon": self.icon,
            "accent": self.accent,
            "greeting": self.greeting,
            "sample_questions": list(self.sample_questions),
            "knowledge_records": self.knowledge_record_count,
            "intents": [
                {"id": i.id, "label": i.label, "description": i.description}
                for i in self.intents
            ],
            "default_voice_gender": self.default_voice_gender,
            "persona_name_female": self.persona_name_female,
            "persona_name_male": self.persona_name_male,
        }
