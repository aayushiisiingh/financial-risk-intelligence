"""End-to-end engine: items -> link -> sentiment -> event class -> impact -> events.jsonl (ENG-06)."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from src.config import EVENTS_PATH, OUT_DIR, RAW_DIR, load_yaml
from src.engine.event_class import classify
from src.engine.impact import NoveltyTracker, compute_impact, relevance_kind
from src.engine.linker import Linker
from src.engine.sentiment import SentimentScorer, get_backend
from src.ingest.loaders import dedup_key, load_all
from src.schemas import RiskEvent, SourceMeta


def run(raw_dir: Path = RAW_DIR, out_path: Path = EVENTS_PATH, backend: str | None = None,
        max_items_per_file: int | None = 3000, cache_path: Path | None = None) -> list[RiskEvent]:
    items = load_all(raw_dir, max_items_per_file=max_items_per_file)
    cfg = load_yaml("impact.yaml")
    linker = Linker()
    scorer = SentimentScorer(get_backend(backend), cache_path=cache_path if cache_path is not None
                             else OUT_DIR / "sentiment_cache.json")
    sentiments = scorer.score_all([i.text for i in items])
    tracker = NoveltyTracker(cfg["novelty"]["window_hours"])
    events: list[RiskEvent] = []
    for it, sent in zip(items, sentiments):  # items are already time-sorted
        ev = classify(it.text)
        for ent in linker.link(it.text, it.ticker_hint):
            key = (ent.ticker or ent.sector or "MACRO", ev.cls.value)
            nov = tracker.observe(key, it.published_at)
            imp = compute_impact(sent.score, it.source_type, ev.cls, relevance_kind(ent), nov, cfg)
            eid = hashlib.sha1(f"{it.source_name}|{it.text}|{ent.ticker}".encode()).hexdigest()[:16]
            events.append(RiskEvent(
                event_id=eid, dedup_key=dedup_key(it.text),
                source=SourceMeta(type=it.source_type, name=it.source_name, url=it.url,
                                  published_at=it.published_at,
                                  ingested_at=it.published_at,  # replay clock
                                  credibility=cfg["source_credibility"][it.source_type]),
                text=it.text, entity=ent, sentiment=sent, event=ev, impact=imp))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for e in events:
            f.write(json.dumps(e.model_dump(mode="json", by_alias=True)) + "\n")
    return events


def summarize(events: list[RiskEvent]) -> str:
    c_src = Counter(e.source.name for e in events)
    c_cls = Counter(e.event.cls.value for e in events)
    c_imp = Counter(e.impact.score for e in events)
    models = {e.sentiment.model for e in events}
    return (f"{len(events)} events | sources={dict(c_src)} | classes={dict(c_cls)} | "
            f"impact={dict(sorted(c_imp.items()))} | sentiment_model={models}")
