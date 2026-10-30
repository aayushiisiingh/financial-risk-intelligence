"""Sanity benchmark on a labelled financial-sentiment file (e.g. FinancialPhraseBank all-data.csv, no header, latin-1).
CAVEAT: ProsusAI/finbert was fine-tuned on FinancialPhraseBank, so FinBERT scores here are optimistic (train/test overlap).
Use the hand-labelled sample from YOUR feed (sentiment_eval.py) as the fair test."""
from __future__ import annotations

import json

import pandas as pd

from src.config import DATA_DIR
from src.engine.sentiment import VaderBackend, get_backend, label_for

RESULTS = DATA_DIR.parent / "docs" / "results"
CANDIDATES = [DATA_DIR / "labels" / "all-data.csv", DATA_DIR / "raw_full" / "all-data.csv"]


def run(max_rows: int = 1500) -> None:
    from sklearn.metrics import f1_score
    path = next((p for p in CANDIDATES if p.exists()), None)
    if path is None:
        print("PhraseBank file not found (put all-data.csv in data/labels/). Skipping.")
        return
    df = pd.read_csv(path, header=None, names=["label", "text"], encoding="latin-1").dropna()
    df = df.sample(min(max_rows, len(df)), random_state=42)
    y = df["label"].str.lower().str.strip()
    texts = df["text"].tolist()
    res = {"n": len(df), "file": path.name,
           "vader_macro_f1": f1_score(y, [label_for(s) for s, _ in VaderBackend().score(texts)], average="macro")}
    try:
        fb = get_backend("finbert")
        res["finbert_macro_f1_OPTIMISTIC_train_overlap"] = f1_score(
            y, [label_for(s) for s, _ in fb.score(texts)], average="macro")
    except (ImportError, OSError, RuntimeError, ValueError) as e:
        res["finbert"] = f"skipped ({type(e).__name__})"
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "phrasebank_eval.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    run()
