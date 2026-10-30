"""Event-driven stress testing (STR-02..STR-04). Shocks are ILLUSTRATIVE scenario assumptions."""
from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path

from src.config import EVENTS_PATH, STRESS_PATH, load_yaml
from src.schemas import Exposure, RiskEvent, Scenario, StressResult

ASSUMPTIONS = [
    "Parallel rate shift; first-order duration/DV01 approximations (no convexity)",
    "Loan impact = change in expected loss (PD x multiplier, capped at 1) x LGD x EAD, deducted from value",
    "Equity shock plus sector overlay applied to equity positions only",
    "Shock magnitudes are illustrative scenario assumptions, not forecasts",
    "Synthetic portfolio: fictional exposures, not real credit views",
]


def load_scenarios() -> list[Scenario]:
    return [Scenario(**s) for s in load_yaml("scenarios.yaml")["scenarios"]]


def exposure_delta(e: Exposure, sc: Scenario) -> tuple[float, float]:
    """Returns (value_delta, expected_loss_change). For loans value_delta == -expected_loss_change."""
    s, p = sc.shocks, e.risk_params
    rate, spread = s.rate_bps / 1e4, s.credit_spread_bps / 1e4
    if e.asset_type == "bond":
        return e.market_value_usd * (-p["modified_duration"] * rate - p["spread_duration"] * spread), 0.0
    if e.asset_type == "loan":
        pd0 = p["pd"]
        pd1 = min(pd0 * s.pd_multiplier, 1.0)
        d_el = p["ead"] * p["lgd"] * (pd1 - pd0)
        return -d_el, d_el
    if e.asset_type == "irs":
        sign = 1.0 if p["position"] == "pay_fixed" else -1.0
        return sign * p["dv01"] * s.rate_bps, 0.0
    if e.asset_type == "fx_forward":
        return p["delta_notional"] * s.fx_pct, 0.0
    if e.asset_type == "equity":
        overlay = sc.sector_overlays.get(e.sector, {}).get("equity_pct", 0.0)
        return e.market_value_usd * (s.equity_pct + overlay), 0.0
    raise ValueError(e.asset_type)


def run_scenario(book: list[Exposure], sc: Scenario, stress_id: str, triggered_by: list[str],
                 ts: datetime) -> StressResult:
    before = sum(e.market_value_usd for e in book)
    by_type: dict[str, float] = {}
    by_sector: dict[str, float] = {}
    rows, d_el_total = [], 0.0
    for e in book:
        d, d_el = exposure_delta(e, sc)
        by_type[e.asset_type] = by_type.get(e.asset_type, 0.0) + d
        by_sector[e.sector] = by_sector.get(e.sector, 0.0) + d
        d_el_total += d_el
        rows.append({"exposure_id": e.exposure_id, "counterparty": e.counterparty, "delta": d})
    delta = sum(by_type.values())
    rows.sort(key=lambda r: abs(r["delta"]), reverse=True)
    return StressResult(stress_id=stress_id, scenario_id=sc.scenario_id, triggered_by=triggered_by, timestamp=ts,
                        portfolio_value_before=before, portfolio_value_after=before + delta, delta=delta,
                        delta_pct=delta / before if before else 0.0, expected_loss_change=d_el_total,
                        by_asset_type=by_type, by_sector=by_sector, by_exposure=rows, assumptions=ASSUMPTIONS)


def triggered(ev: RiskEvent, sc: Scenario) -> bool:
    return ev.event.cls.value == sc.trigger["event_class"] and ev.impact.score >= sc.trigger["min_impact"]


def run_triggers(events: Iterable[RiskEvent], book: list[Exposure], scenarios: list[Scenario]) -> list[StressResult]:
    last: dict[str, datetime] = {}
    results: list[StressResult] = []
    for ev in sorted(events, key=lambda e: e.source.published_at):
        for sc in scenarios:
            if not triggered(ev, sc):
                continue
            t = ev.source.published_at
            if sc.scenario_id in last and t - last[sc.scenario_id] < timedelta(minutes=sc.cooldown_minutes):
                continue  # cooldown (D11)
            last[sc.scenario_id] = t
            results.append(run_scenario(book, sc, f"ST-{len(results) + 1:04d}", [ev.event_id], t))
    return results


def read_events(path: Path = EVENTS_PATH) -> list[RiskEvent]:
    return [RiskEvent.model_validate(json.loads(l)) for l in Path(path).read_text().splitlines() if l.strip()]


def write_results(results: list[StressResult], path: Path = STRESS_PATH) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w") as f:
        f.writelines(json.dumps(r.model_dump(mode="json")) + "\n" for r in results)
