from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw_samples"
PRICES_DIR = DATA_DIR / "prices"
OUT_DIR = DATA_DIR / "output"
EVENTS_PATH = OUT_DIR / "events.jsonl"
STRESS_PATH = OUT_DIR / "stress_results.jsonl"
PORTFOLIO_PATH = DATA_DIR / "portfolio.json"


def load_yaml(name: str) -> dict:
    return yaml.safe_load((CONFIG_DIR / name).read_text())
