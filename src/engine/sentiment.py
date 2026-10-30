"""Sentiment (ENG-03): FinBERT with VADER fallback. Output score in [-1, 1]."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.config import OUT_DIR, load_yaml
from src.schemas import Sentiment


class VaderBackend:
    name = "vader"

    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self.an = SentimentIntensityAnalyzer()

    def score(self, texts: list[str]) -> list[tuple[float, float]]:
        out = []
        for t in texts:
            c = self.an.polarity_scores(t)["compound"]
            out.append((float(c), float(min(1.0, abs(c)))))
        return out


class FinBertBackend:
    name = "finbert"

    def __init__(self, model: str = "ProsusAI/finbert"):
        from transformers import pipeline
        self.pipe = pipeline("text-classification", model=model, top_k=None, truncation=True, max_length=128)

    def score(self, texts: list[str], batch: int = 32) -> list[tuple[float, float]]:
        out = []
        for i in range(0, len(texts), batch):
            for res in self.pipe(texts[i:i + batch]):
                p = {r["label"].lower(): r["score"] for r in res}
                out.append((float(p.get("positive", 0) - p.get("negative", 0)), float(max(p.values()))))
        return out


def get_backend(name: str | None = None):
    cfg = load_yaml("event_rules.yaml")["sentiment"]
    name = name or cfg["backend"]
    if name == "vader":
        return VaderBackend()
    try:
        return FinBertBackend(cfg["finbert_model"])
    except (ImportError, OSError, RuntimeError, ValueError) as e:
        if name == "finbert":
            raise
        print(f"WARNING: FinBERT unavailable ({type(e).__name__}: {e}). Falling back to VADER. "
              "Outputs will say model='vader'.")
        return VaderBackend()


def label_for(score: float) -> str:
    th = load_yaml("impact.yaml")["sentiment_label_thresholds"]
    return "positive" if score >= th["positive"] else "negative" if score <= th["negative"] else "neutral"


class SentimentScorer:
    def __init__(self, backend=None, cache_path: Path | None = None):
        self.backend = backend or get_backend()
        self.cache_path = cache_path if cache_path is not None else OUT_DIR / "sentiment_cache.json"
        self.cache: dict[str, list[float]] = {}
        if self.cache_path and Path(self.cache_path).exists():
            try:
                self.cache = json.loads(Path(self.cache_path).read_text())
            except (ValueError, OSError):
                self.cache = {}

    def _k(self, text: str) -> str:
        return hashlib.sha1((self.backend.name + "|" + text).encode()).hexdigest()

    def score_all(self, texts: list[str]) -> list[Sentiment]:
        todo = [t for t in dict.fromkeys(texts) if self._k(t) not in self.cache]
        if todo:
            for t, (s, c) in zip(todo, self.backend.score(todo)):
                self.cache[self._k(t)] = [s, c]
            if self.cache_path:
                Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
                Path(self.cache_path).write_text(json.dumps(self.cache))
        res = []
        for t in texts:
            s, c = self.cache[self._k(t)]
            s = max(-1.0, min(1.0, s))
            res.append(Sentiment(score=round(s, 4), label=label_for(s), confidence=round(max(0.0, min(1.0, c)), 4),
                                 model=self.backend.name))
        return res
