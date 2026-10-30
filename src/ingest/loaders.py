"""Load news / tweet CSVs into a common SourceItem (ENG-01)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

TEXT_CANDS = ["headline", "headlines", "sentence", "title", "text", "tweet", "content", "body", "description", "summary", "news"]
DATE_CANDS = ["published_at", "date", "datetime", "created_at", "timestamp", "time", "publish_date", "pubdate"]
TICKER_CANDS = ["ticker", "stock name", "stock", "symbol"]

_HANDLE = re.compile(r"@\w+")
_URL = re.compile(r"https?://\S+")
_WS = re.compile(r"\s+")


@dataclass
class SourceItem:
    text: str
    source_type: str  # news | social
    source_name: str
    published_at: datetime
    url: str | None = None
    ticker_hint: str | None = None


def clean_text(text: str, strip_handles: bool = True) -> str:
    text = _URL.sub("", str(text))
    if strip_handles:
        text = _HANDLE.sub("", text)
    return _WS.sub(" ", text).strip()


def dedup_key(text: str) -> str:
    norm = re.sub(r"[^a-z0-9 ]", "", text.lower())
    norm = _WS.sub(" ", norm).strip()
    return hashlib.sha1(norm.encode()).hexdigest()


def _pick(columns, cands):
    lower = {c.lower(): c for c in columns}
    for cand in cands:
        if cand in lower:
            return lower[cand]
    return None


def load_csv(path: Path, source_type: str, source_name: str, nrows: int | None = None) -> list[SourceItem]:
    df = pd.read_csv(path, nrows=nrows, encoding_errors="replace", on_bad_lines="skip")
    if str(df.columns[0]).strip().lower() in {"positive", "neutral", "negative"}:  # headerless (label, text) file
        df = pd.read_csv(path, nrows=nrows, header=None, names=["label", "text"], encoding="latin-1", on_bad_lines="skip")
    text_col = _pick(df.columns, TEXT_CANDS)
    if text_col is None:  # fallback: the string column with the longest average text
        str_cols = [c for c in df.columns if df[c].dtype == object]
        if not str_cols:
            raise ValueError(f"{path.name}: no text column found among {list(df.columns)}")
        text_col = max(str_cols, key=lambda c: df[c].astype(str).str.len().mean())
        print(f"WARNING: {path.name}: guessed text column '{text_col}'")
    date_col = _pick(df.columns, DATE_CANDS)
    tick_col = _pick(df.columns, TICKER_CANDS)
    df = df.dropna(subset=[text_col]).reset_index(drop=True)
    if date_col is not None:
        ts = pd.to_datetime(df[date_col], errors="coerce", utc=True)
        if ts.isna().mean() > 0.5:
            print(f"WARNING: {path.name}: more than half of '{date_col}' values could not be parsed as dates.")
    else:
        print(f"WARNING: {path.name} has no date column; assigning sequential replay timestamps "
              "(price-based evaluation will not be meaningful for this file).")
        base = datetime(2021, 1, 4, 14, 0, tzinfo=UTC)
        ts = pd.Series([base + timedelta(minutes=5 * i) for i in range(len(df))])
    items: list[SourceItem] = []
    for i, row in df.iterrows():
        t = ts.iloc[i]
        if pd.isna(t):
            continue
        text = clean_text(row[text_col], strip_handles=(source_type == "social"))
        if len(text) < 10:
            continue
        hint = None
        if tick_col is not None and pd.notna(row[tick_col]):
            hint = str(row[tick_col]).strip().upper()
        items.append(SourceItem(text, source_type, source_name, t.to_pydatetime(), None, hint))
    return items


def load_all(raw_dir: Path, max_items_per_file: int | None = None) -> list[SourceItem]:
    files = sorted(Path(raw_dir).glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSV files in {raw_dir}. Put your news/tweet CSVs there (files with 'tweet' in the name are "
            "treated as social), or run `make sample` for the synthetic fallback."
        )
    items: list[SourceItem] = []
    for f in files:
        stype = "social" if "tweet" in f.stem.lower() else "news"
        items.extend(load_csv(f, stype, f.stem, nrows=max_items_per_file))
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x.published_at):
        k = dedup_key(it.text)
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out
