"""EVL-02: impact score vs absolute abnormal return (stock minus SPY), if prices are cached.
Convention: event day = UTC date of the item (next trading day if not a trading day); return = close-to-close on that day.
Bucketed means are reported as measured; this is NOT a claim of predictive power."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import EVENTS_PATH, PRICES_DIR, load_yaml

RESULTS = Path(__file__).resolve().parents[2] / "docs" / "results"


def _ret(t: str) -> pd.Series | None:
    p = PRICES_DIR / f"{t}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    col = "Close" if "Close" in df.columns else df.columns[0]
    return df[col].astype(float).pct_change().dropna()


def run() -> None:
    from scipy.stats import spearmanr
    bench = load_yaml("universe.yaml")["market_benchmark"]
    spy = _ret(bench)
    if spy is None:
        print("No cached prices (run `make data` with internet). Skipping impact evaluation.")
        return
    rows = [json.loads(l) for l in Path(EVENTS_PATH).read_text().splitlines() if l.strip()]
    cache: dict[str, pd.Series | None] = {}
    recs = []
    for r in rows:
        t = r["entity"]["ticker"]
        if not t:
            continue
        if t not in cache:
            cache[t] = _ret(t)
        s = cache[t]
        if s is None:
            continue
        d = pd.Timestamp(r["source"]["published_at"]).tz_localize(None).normalize()
        idx = s.index.searchsorted(d)
        if idx >= len(s) or s.index[idx] not in spy.index:
            continue
        day = s.index[idx]
        recs.append({"impact": r["impact"]["score"], "abs_abn": abs(float(s.iloc[idx] - spy.loc[day]))})
    if len(recs) < 20:
        print(f"Only {len(recs)} events matched price data; not enough for evaluation.")
        return
    df = pd.DataFrame(recs)
    rho, pval = spearmanr(df["impact"], df["abs_abn"])
    df["bucket"] = pd.cut(df["impact"], [0, 3, 6, 10], labels=["1-3", "4-6", "7-10"])
    buckets = df.groupby("bucket", observed=True)["abs_abn"].agg(["mean", "count"]).reset_index()
    RESULTS.mkdir(parents=True, exist_ok=True)
    buckets.to_csv(RESULTS / "impact_buckets.csv", index=False)
    (RESULTS / "impact_eval.json").write_text(json.dumps({"n": len(df), "spearman_rho": rho, "p_value": pval}, indent=2))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ax = buckets.plot.bar(x="bucket", y="mean", legend=False, title="Mean |abnormal return| by impact bucket")
    ax.set_ylabel("mean |stock - SPY| daily return")
    plt.tight_layout()
    plt.savefig(RESULTS / "impact_buckets.png", dpi=150)
    print(f"n={len(df)} spearman={rho:.3f} p={pval:.3g}")
    print(buckets)
