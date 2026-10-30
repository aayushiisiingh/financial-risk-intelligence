"""SYNTHETIC wholesale banking book (STR-01). Fictional exposures; NOT real credit views."""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

from src.config import PORTFOLIO_PATH, load_yaml
from src.schemas import Exposure

PD_BY_RATING = {"AAA": 0.0003, "AA": 0.0007, "A": 0.002, "BBB": 0.008, "BB": 0.025, "B": 0.07}


def generate(seed: int = 42, n: int = 40) -> list[Exposure]:
    rng = random.Random(seed)
    stocks = load_yaml("universe.yaml")["stocks"]
    by_sector: dict[str, list[dict]] = {}
    for s in stocks:
        by_sector.setdefault(s["sector"], []).append(s)
    sectors = list(by_sector)
    kinds = ["loan"] * 14 + ["bond"] * 12 + ["irs"] * 5 + ["fx_forward"] * 4 + ["equity"] * 5
    kinds = (kinds * ((n // len(kinds)) + 1))[:n]
    rng.shuffle(kinds)
    out: list[Exposure] = []
    for i, kind in enumerate(kinds, start=1):
        sector = rng.choice(sectors)
        tick = rng.choice(by_sector[sector])["ticker"]
        rating = rng.choice(list(PD_BY_RATING))
        notional = float(rng.choice([5, 10, 15, 25, 40, 50])) * 1e6
        letter = chr(64 + (i % 26 or 26))
        cp = f"Corporate {sector} {letter}{i}"
        maturity = date(2026, 10, 11) + timedelta(days=rng.randint(180, 365 * 8))
        if kind == "loan":
            params = {"pd": PD_BY_RATING[rating], "lgd": 0.45, "ead": notional}
            mv = notional * 0.99
        elif kind == "bond":
            d = round(rng.uniform(2.0, 8.0), 2)
            params = {"coupon": round(rng.uniform(0.03, 0.06), 4), "modified_duration": d,
                      "spread_duration": round(d * 0.95, 2)}
            mv = notional * rng.uniform(0.95, 1.03)
        elif kind == "irs":
            dur = rng.uniform(2.0, 7.0)
            params = {"dv01": round(notional * dur * 1e-4, 2), "position": rng.choice(["pay_fixed", "receive_fixed"])}
            mv = notional * rng.uniform(-0.01, 0.01)
        elif kind == "fx_forward":
            params = {"delta_notional": notional * rng.choice([-1, 1])}
            mv = notional * rng.uniform(-0.005, 0.005)
            cp = f"FX Counterparty {letter}{i}"
        else:
            params = {"position": "long"}
            mv = notional * 0.4
            cp = f"Trading Book Equity {sector} {i}"
        out.append(Exposure(exposure_id=f"EXP-{i:03d}", counterparty=cp, linked_ticker=tick, sector=sector,
                            asset_type=kind, rating=rating, notional_usd=notional, market_value_usd=round(mv, 2),
                            maturity_date=maturity, risk_params=params))
    return out


def save(path: Path = PORTFOLIO_PATH, **kw) -> list[Exposure]:
    book = generate(**kw)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"SYNTHETIC": True,
                                      "note": "Fictional exposures for demonstration only. Not real credit views.",
                                      "exposures": [e.model_dump(mode="json") for e in book]}, indent=2))
    return book


def load(path: Path = PORTFOLIO_PATH) -> list[Exposure]:
    if not Path(path).exists():
        return save(path)
    return [Exposure(**e) for e in json.loads(Path(path).read_text())["exposures"]]
