"""Entity linking (ENG-02): cashtag -> bare ticker/alias -> ticker hint -> fuzzy -> sector-level."""
from __future__ import annotations

import re

from src.config import load_yaml
from src.schemas import EntityRef

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None

_CASHTAG = re.compile(r"\$([A-Za-z]{1,5})\b")


class Linker:
    def __init__(self, max_entities: int = 3):
        uni = load_yaml("universe.yaml")
        rules = load_yaml("event_rules.yaml")
        self.max_entities = max_entities
        self.by_ticker = {s["ticker"]: s for s in uni["stocks"]}
        self.alias_patterns = []
        self.fuzzy_aliases: list[tuple[str, dict]] = []
        for s in uni["stocks"]:
            for a in set(s["aliases"] + [s["name"].lower()]):
                self.alias_patterns.append((re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)"), s))
                if len(a) >= 6:
                    self.fuzzy_aliases.append((a, s))
        self.bare = [(re.compile(r"\b" + t + r"\b"), s) for t, s in self.by_ticker.items() if len(t) >= 3]
        self.sector_patterns = {
            sec: [re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)") for k in kws]
            for sec, kws in rules["sector_keywords"].items()
        }

    def _ref(self, s: dict, method: str, conf: float) -> EntityRef:
        return EntityRef(ticker=s["ticker"], name=s["name"], sector=s["sector"], match_method=method, match_confidence=conf)

    def link(self, text: str, hint: str | None = None) -> list[EntityRef]:
        found: dict[str, EntityRef] = {}
        for m in _CASHTAG.findall(text):
            t = m.upper()
            if t in self.by_ticker:
                found.setdefault(t, self._ref(self.by_ticker[t], "cashtag", 0.98))
        low = text.lower()
        for pat, s in self.alias_patterns:
            if pat.search(low):
                found.setdefault(s["ticker"], self._ref(s, "alias", 0.9))
        for pat, s in self.bare:
            if pat.search(text):
                found.setdefault(s["ticker"], self._ref(s, "alias", 0.9))
        if not found and hint and hint in self.by_ticker:
            found[hint] = self._ref(self.by_ticker[hint], "alias", 0.7)
        if not found and fuzz is not None:
            best, best_s = 0.0, None
            for a, s in self.fuzzy_aliases:
                sc = fuzz.partial_ratio(a, low)
                if sc > best:
                    best, best_s = sc, s
            if best_s is not None and best >= 90:
                found[best_s["ticker"]] = self._ref(best_s, "fuzzy", round(best / 100, 2))
        if found:
            return list(found.values())[: self.max_entities]
        for sector, pats in self.sector_patterns.items():
            if any(p.search(low) for p in pats):
                return [EntityRef(sector=sector, match_method="sector_level", match_confidence=0.5)]
        return [EntityRef(match_method="none", match_confidence=0.0)]
