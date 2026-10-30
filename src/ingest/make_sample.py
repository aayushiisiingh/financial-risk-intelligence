"""Generate a SYNTHETIC fallback dataset (clearly labelled) so the demo runs without downloads."""
from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pandas as pd

from src.config import RAW_DIR, load_yaml

TEMPLATES = {
    "Geopolitical": [
        ("Sanctions and military tensions push {name} lower as oil route risks grow", -1),
        ("Ceasefire hopes ease geopolitical tensions, {name} rallies", 1),
        ("New tariffs announced; {name} warns of supply disruption", -1),
    ],
    "Macroeconomic": [
        ("Fed signals rate hike as inflation surprises, {name} slides", -1),
        ("Strong jobs report lifts markets, {name} gains", 1),
        ("Recession fears grow, analysts cut outlook for {name}", -1),
    ],
    "Credit Event": [
        ("{name} downgraded by rating agency amid debt concerns", -1),
        ("{name} avoids default after successful debt restructuring", 1),
        ("Lender to {name} warns of bankruptcy risk for supplier", -1),
    ],
    "Merger/Acquisition": [
        ("{name} to acquire rival in major acquisition deal", 1),
        ("Takeover talks collapse for {name}", -1),
    ],
    "Product Launch": [
        ("{name} launches new product line to strong reviews", 1),
        ("{name} unveils flagship release, shares edge up", 1),
    ],
    "Regulatory/Legal": [
        ("{name} faces antitrust probe from regulators", -1),
        ("{name} settlement with SEC removes legal overhang", 1),
    ],
    "Earnings": [
        ("{name} quarterly earnings beat estimates, raises guidance", 1),
        ("{name} profit misses estimates, weak revenue outlook", -1),
    ],
    "Operational/Cyber": [
        ("{name} hit by cyberattack and data breach", -1),
        ("Production halt at {name} after supply chain outage", -1),
    ],
}


def make(seed: int = 7, n_news: int = 260, n_tweets: int = 260) -> None:
    rng = random.Random(seed)
    stocks = load_yaml("universe.yaml")["stocks"]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    start = datetime(2021, 3, 1, 14, 30, tzinfo=UTC)
    classes = list(TEMPLATES)

    def stamp():
        return start + timedelta(days=rng.randint(0, 27), minutes=rng.randint(0, 390))

    news = []
    for _ in range(n_news):
        s = rng.choice(stocks)
        text, _ = rng.choice(TEMPLATES[rng.choice(classes)])
        news.append({"headline": text.format(name=s["name"]), "published_at": stamp().isoformat(), "source": "SYNTHETIC"})
    tweets = []
    for _ in range(n_tweets):
        s = rng.choice(stocks)
        text, _ = rng.choice(TEMPLATES[rng.choice(classes)])
        tw = f"@user{rng.randint(1, 999)} ${s['ticker']} " + text.format(name=s["name"]) + rng.choice(["", " lol", " !!", " #stocks"])
        tweets.append({"tweet": tw, "created_at": stamp().isoformat(), "stock": s["ticker"], "source": "SYNTHETIC"})
    pd.DataFrame(news).to_csv(RAW_DIR / "synthetic_news.csv", index=False)
    pd.DataFrame(tweets).to_csv(RAW_DIR / "synthetic_tweets.csv", index=False)
    print(f"Wrote SYNTHETIC sample data to {RAW_DIR}")


if __name__ == "__main__":
    make()
