"""Rule-based event classifier (ENG-04)."""
from __future__ import annotations

import re

from src.config import load_yaml
from src.schemas import EventClass, EventInfo

_RULES = None


def _rules():
    global _RULES
    if _RULES is None:
        kw = load_yaml("event_rules.yaml")["event_keywords"]
        _RULES = {
            cls: [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)") for k in words] for cls, words in kw.items()
        }
    return _RULES


def classify(text: str) -> EventInfo:
    low = text.lower()
    best_cls, best_hits = None, 0
    for cls, pats in _rules().items():
        hits = sum(1 for p in pats if p.search(low))
        if hits > best_hits:  # strict > keeps config order as tie-break priority
            best_cls, best_hits = cls, hits
    if best_cls is None:
        return EventInfo(**{"class": EventClass.OTHER, "confidence": 0.3, "method": "rules"})
    return EventInfo(**{"class": EventClass(best_cls), "confidence": round(min(1.0, 0.5 + 0.15 * best_hits), 2),
                        "method": "rules"})
