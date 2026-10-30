"""Download daily prices with yfinance and cache to data/prices/*.csv (needs internet once)."""
from __future__ import annotations

import sys

from src.config import PRICES_DIR, load_yaml


def main(start: str = "2020-01-01", end: str = "2022-12-31") -> None:
    import yfinance as yf

    uni = load_yaml("universe.yaml")
    tickers = [s["ticker"] for s in uni["stocks"]] + [uni["market_benchmark"]]
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    for t in tickers:
        df = yf.download(t, start=start, end=end, progress=False, auto_adjust=True)
        if df is None or df.empty:
            print(f"WARNING: no data for {t}")
            continue
        if hasattr(df.columns, "levels"):  # flatten MultiIndex columns
            df.columns = [c[0] for c in df.columns]
        df[["Close"]].to_csv(PRICES_DIR / f"{t}.csv")
        print(f"cached {t}: {len(df)} rows")


if __name__ == "__main__":
    main(*sys.argv[1:3])
