from datetime import UTC, date, datetime, timedelta

import pytest

from src.modules.stress_test import exposure_delta, run_scenario, run_triggers
from src.schemas import Exposure, Scenario, Shocks


def exp(kind, params, mv=1_000_000.0, sector="Energy", eid="E1"):
    return Exposure(exposure_id=eid, counterparty="X", sector=sector, asset_type=kind, rating="BBB",
                    notional_usd=mv, market_value_usd=mv, maturity_date=date(2030, 1, 1), risk_params=params)


def sc(**shocks):
    return Scenario(scenario_id="T", trigger={"event_class": "Geopolitical", "min_impact": 7}, shocks=Shocks(**shocks))


def test_bond_duration_4_plus_100bp_is_minus_4pct():
    e = exp("bond", {"modified_duration": 4.0, "spread_duration": 4.0})
    d, el = exposure_delta(e, sc(rate_bps=100))
    assert d == pytest.approx(-40_000) and el == 0


def test_loan_expected_loss():
    e = exp("loan", {"pd": 0.01, "lgd": 0.45, "ead": 1_000_000})
    d, el = exposure_delta(e, sc(pd_multiplier=2.0))
    assert el == pytest.approx(4_500) and d == pytest.approx(-4_500)


def test_loan_pd_capped():
    e = exp("loan", {"pd": 0.6, "lgd": 0.5, "ead": 100.0})
    _, el = exposure_delta(e, sc(pd_multiplier=5.0))
    assert el == pytest.approx(100 * 0.5 * 0.4)


def test_irs_signs():
    pay = exp("irs", {"dv01": 1000.0, "position": "pay_fixed"})
    rec = exp("irs", {"dv01": 1000.0, "position": "receive_fixed"})
    assert exposure_delta(pay, sc(rate_bps=100))[0] == pytest.approx(100_000)
    assert exposure_delta(rec, sc(rate_bps=100))[0] == pytest.approx(-100_000)


def test_fx_and_equity_overlay():
    assert exposure_delta(exp("fx_forward", {"delta_notional": 5_000_000.0}), sc(fx_pct=0.02))[0] == pytest.approx(100_000)
    s = Scenario(scenario_id="T", trigger={"event_class": "Geopolitical", "min_impact": 7}, shocks=Shocks(equity_pct=-0.10),
                 sector_overlays={"Energy": {"equity_pct": 0.05}})
    assert exposure_delta(exp("equity", {"position": "long"}), s)[0] == pytest.approx(-50_000)


def test_zero_shock_zero_change_and_sums():
    book = [exp("bond", {"modified_duration": 4.0, "spread_duration": 3.8}, eid="B"),
            exp("loan", {"pd": 0.01, "lgd": 0.45, "ead": 1e6}, eid="L"),
            exp("irs", {"dv01": 500.0, "position": "pay_fixed"}, eid="I")]
    z = run_scenario(book, sc(), "ST-1", [], datetime(2021, 1, 1, tzinfo=UTC))
    assert z.delta == 0
    r = run_scenario(book, sc(rate_bps=50, credit_spread_bps=100, pd_multiplier=2.0), "ST-2", [],
                     datetime(2021, 1, 1, tzinfo=UTC))
    assert sum(r.by_asset_type.values()) == pytest.approx(r.delta)
    assert sum(x["delta"] for x in r.by_exposure) == pytest.approx(r.delta)
    assert r.portfolio_value_after == pytest.approx(r.portfolio_value_before + r.delta)


def test_trigger_threshold_and_cooldown():
    from src.engine.impact import compute_impact
    from src.schemas import (
        EntityRef,
        EventClass,
        EventInfo,
        RiskEvent,
        Sentiment,
        SourceMeta,
    )

    def ev(i, minutes, score_hi=True):
        t = datetime(2021, 3, 1, 15, 0, tzinfo=UTC) + timedelta(minutes=minutes)
        imp = compute_impact(-0.9 if score_hi else 0.0, "news", EventClass.GEOPOLITICAL, "direct_entity", 1.0)
        if not score_hi:
            imp.score = 3
        return RiskEvent(event_id=f"e{i}", dedup_key="k", source=SourceMeta(type="news", name="n", published_at=t,
                         ingested_at=t, credibility=0.85), text="t", entity=EntityRef(),
                         sentiment=Sentiment(score=-0.9, label="negative", confidence=0.9, model="m"),
                         event=EventInfo(**{"class": EventClass.GEOPOLITICAL, "confidence": 0.9, "method": "rules"}),
                         impact=imp)
    book = [exp("bond", {"modified_duration": 4.0, "spread_duration": 4.0})]
    scen = Scenario(scenario_id="G", trigger={"event_class": "Geopolitical", "min_impact": 7}, shocks=Shocks(rate_bps=100),
                    cooldown_minutes=60)
    res = run_triggers([ev(1, 0, score_hi=False), ev(2, 5), ev(3, 20), ev(4, 90)], book, [scen])
    assert [r.triggered_by[0] for r in res] == ["e2", "e4"]
