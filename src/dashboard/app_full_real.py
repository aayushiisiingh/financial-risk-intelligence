"""Streamlit dashboard (DSH-01). Run: streamlit run src/dashboard/app.py"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
EVENTS = ROOT / "data/output/events_full_real.jsonl"
STRESS = ROOT / "data/output/stress_results_full_real.jsonl"

st.set_page_config(page_title="Financial Risk Engine", layout="wide")
st.title("Financial Risk Engine: NLP signals and event-driven stress testing")
st.warning("Research prototype, not investment advice. Portfolio is SYNTHETIC (fictional exposures, not real credit "
           "views). Shock magnitudes are illustrative scenario assumptions.")


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


events, stress = read_jsonl(EVENTS), read_jsonl(STRESS)
if not events:
    st.error("No events found. Run `make pipeline` (or `make sample` first, then `make demo`).")
    st.stop()

df = pd.json_normalize(events)
df = df.rename(columns={"source.type": "source_type", "source.name": "source_name", "source.published_at": "published_at",
                        "entity.ticker": "ticker", "entity.sector": "sector", "sentiment.score": "sentiment",
                        "sentiment.model": "model", "event.class": "event_class", "impact.score": "impact"})
df["published_at"] = pd.to_datetime(df["published_at"], utc=True)

tab1, tab2 = st.tabs(["Risk signals", "Stress tests"])
with tab1:
    c1, c2, c3 = st.columns(3)
    classes = c1.multiselect("Event class", sorted(df["event_class"].unique()))
    tickers = c2.multiselect("Ticker", sorted(df["ticker"].dropna().unique()))
    min_imp = c3.slider("Min impact", 1, 10, 1)
    f = df[df["impact"] >= min_imp]
    if classes:
        f = f[f["event_class"].isin(classes)]
    if tickers:
        f = f[f["ticker"].isin(tickers)]
    m1, m2, m3 = st.columns(3)
    m1.metric("Events", len(f))
    m2.metric("Mean sentiment", f"{f['sentiment'].mean():.2f}" if len(f) else "n/a")
    m3.metric("Sentiment model", ", ".join(sorted(df["model"].unique())))
    g1, g2 = st.columns(2)
    g1.plotly_chart(px.histogram(f, x="impact", nbins=10, title="Impact score distribution"), width="stretch")
    g2.plotly_chart(px.histogram(f, x="event_class", color="source_type", title="Events by class and source"),
                    width="stretch")
    st.dataframe(f.sort_values("published_at", ascending=False)[
        ["published_at", "source_type", "ticker", "sector", "event_class", "sentiment", "impact", "text"]].head(500),
        width="stretch")
    with st.expander("Why this impact score? (components of one event)"):
        if len(f):
            ev = events[int(f.sort_values("impact", ascending=False).index[0])]
            st.json(ev["impact"])
            st.caption("impact = clip(round(1 + 9 x severity x relevance x (0.4|sentiment| + 0.3 credibility + 0.3 novelty)), 1, 10)")

with tab2:
    if not stress:
        st.info("No stress tests triggered. Lower the impact thresholds in config/scenarios.yaml or run `make stress`.")
    else:
        labels = [f"{s['stress_id']} | {s['scenario_id']} | {s['timestamp'][:16]}" for s in stress]
        sel = st.selectbox("Stress test", labels)
        s = stress[labels.index(sel)]
        a, b, c = st.columns(3)
        a.metric("Value before", f"${s['portfolio_value_before']:,.0f}")
        b.metric("Value after", f"${s['portfolio_value_after']:,.0f}", f"{s['delta_pct']:.2%}")
        c.metric("Expected-loss change", f"${s['expected_loss_change']:,.0f}")
        fig = go.Figure(go.Bar(x=["Before", "After"], y=[s["portfolio_value_before"], s["portfolio_value_after"]]))
        fig.update_layout(title="Portfolio value before vs after (SYNTHETIC book)")
        st.plotly_chart(fig, width="stretch")
        x1, x2 = st.columns(2)
        x1.plotly_chart(px.bar(x=list(s["by_asset_type"]), y=list(s["by_asset_type"].values()),
                               labels={"x": "Asset type", "y": "Delta (USD)"}, title="Impact by asset type"),
                        width="stretch")
        x2.plotly_chart(px.bar(x=list(s["by_sector"]), y=list(s["by_sector"].values()),
                               labels={"x": "Sector", "y": "Delta (USD)"}, title="Impact by sector"),
                        width="stretch")
        trig = next((e for e in events if e["event_id"] in s["triggered_by"]), None)
        if trig:
            st.subheader("Triggering event")
            st.write(f"[{trig['event']['class']}, impact {trig['impact']['score']}] {trig['text']}")
        with st.expander("Assumptions"):
            for t in s["assumptions"]:
                st.write("- " + t)
