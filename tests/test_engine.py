from datetime import UTC, datetime

from src.engine.event_class import classify
from src.engine.impact import NoveltyTracker, compute_impact
from src.engine.linker import Linker
from src.schemas import EventClass


def test_impact_hand_computed():
    # S=0.9, R=1, inner = 0.4*0.8 + 0.3*0.85 + 0.3*1 = 0.875; raw=0.7875; 1+9*0.7875=8.0875 -> 8
    imp = compute_impact(-0.8, "news", EventClass.GEOPOLITICAL, "direct_entity", 1.0)
    assert imp.score == 8 and abs(imp.raw - 0.7875) < 1e-6
    assert imp.components.severity == 0.9


def test_impact_bounds():
    lo = compute_impact(0.0, "social", EventClass.OTHER, "none", 0.0)
    hi = compute_impact(1.0, "news", EventClass.CREDIT, "direct_entity", 1.0)
    assert 1 <= lo.score <= 10 and 1 <= hi.score <= 10 and hi.score > lo.score


def test_novelty_decays():
    tr = NoveltyTracker(24)
    t = datetime(2021, 3, 1, tzinfo=UTC)
    assert tr.observe(("A", "x"), t) == 1.0
    assert tr.observe(("A", "x"), t) == 0.5


def test_event_classes():
    cases = {
        "Company defaults after bankruptcy filing": EventClass.CREDIT,
        "Sanctions and military conflict escalate": EventClass.GEOPOLITICAL,
        "Fed raises interest rate as inflation climbs": EventClass.MACRO,
        "Firm sued in antitrust lawsuit": EventClass.REGULATORY,
        "Company to acquire rival in takeover": EventClass.MNA,
        "Cyberattack causes outage and data breach": EventClass.OPERATIONAL,
        "Quarterly earnings beat estimates": EventClass.EARNINGS,
        "Company launches new product": EventClass.PRODUCT,
        "The weather is nice today": EventClass.OTHER,
    }
    for text, want in cases.items():
        assert classify(text).cls == want, text


def test_linker():
    lk = Linker()
    assert lk.link("$AAPL looks strong")[0].ticker == "AAPL"
    assert lk.link("Exxon Mobil cuts spending")[0].ticker == "XOM"
    assert lk.link("Oil prices jump on supply worries")[0].match_method == "sector_level"
    assert lk.link("nothing relevant here")[0].match_method == "none"
