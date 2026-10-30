"""Explainable impact score (ENG-05). All numbers come from config/impact.yaml."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta

from src.config import load_yaml
from src.schemas import EntityRef, EventClass, Impact, ImpactComponents


class NoveltyTracker:
    """novelty = 1 / (1 + similar items already seen in the trailing window). Feed items in time order."""

    def __init__(self, window_hours: float):
        self.window = timedelta(hours=window_hours)
        self.seen: dict[tuple, deque] = defaultdict(deque)

    def observe(self, key: tuple, ts: datetime) -> float:
        dq = self.seen[key]
        while dq and ts - dq[0] > self.window:
            dq.popleft()
        n = len(dq)
        dq.append(ts)
        return 1.0 / (1.0 + n)


def relevance_kind(entity: EntityRef) -> str:
    if entity.ticker:
        return "direct_entity"
    return "sector_level" if entity.match_method == "sector_level" else "none"


def compute_impact(sentiment_score: float, source_type: str, event_cls: EventClass, rel_kind: str,
                   novelty: float, cfg: dict | None = None) -> Impact:
    cfg = cfg or load_yaml("impact.yaml")
    w = cfg["weights"]
    S = cfg["severity"][event_cls.value]
    R = cfg["relevance"][rel_kind]
    cred = cfg["source_credibility"][source_type]
    inner = w["abs_sentiment"] * abs(sentiment_score) + w["credibility"] * cred + w["novelty"] * novelty
    raw = S * R * inner
    score = int(max(1, min(10, round(1 + 9 * raw))))
    return Impact(score=score, raw=round(raw, 4), components=ImpactComponents(
        severity=S, relevance=R, abs_sentiment=round(abs(sentiment_score), 4), credibility=cred,
        novelty=round(novelty, 4)))
