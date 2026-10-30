"""EVL-01: FinBERT vs VADER macro-F1 on a hand-labelled sample."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd

from src.config import DATA_DIR, EVENTS_PATH
from src.engine.sentiment import VaderBackend, label_for

LABELS = DATA_DIR / "labels" / "sentiment_sample.csv"
RESULTS = DATA_DIR.parent / "docs" / "results"


def make_template(n: int = 50, seed: int = 1) -> None:
    rows = [json.loads(l) for l in Path(EVENTS_PATH).read_text().splitlines() if l.strip()]
    rnd = random.Random(seed)
    uniq = list({r["text"]: r for r in rows}.values())
    sample = rnd.sample(uniq, min(n, len(uniq)))
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"text": [r["text"] for r in sample], "engine_model": [r["sentiment"]["model"] for r in sample],
                  "engine_label": [r["sentiment"]["label"] for r in sample],
                  "human_label": ""}).to_csv(LABELS, index=False)
    print(f"Wrote {LABELS}. Fill human_label (positive/neutral/negative) YOURSELF without looking at engine_label, "
          "then run `make eval`.")


def run() -> None:
    from sklearn.metrics import classification_report, f1_score
    if not LABELS.exists():
        make_template()
        return
    df = pd.read_csv(LABELS).dropna(subset=["human_label"])
    df = df[df["human_label"].astype(str).str.strip() != ""]
    if df.empty:
        print("No human labels yet; fill data/labels/sentiment_sample.csv first.")
        return
    y = df["human_label"].str.lower().str.strip()
    vader = VaderBackend().score(df["text"].tolist())
    v_lab = [label_for(s) for s, _ in vader]
    res = {"n": len(df), "engine (" + str(df["engine_model"].iloc[0]) + ") macro_f1": f1_score(y, df["engine_label"], average="macro"),
           "vader macro_f1": f1_score(y, v_lab, average="macro")}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "sentiment_eval.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print(classification_report(y, df["engine_label"], zero_division=0))
