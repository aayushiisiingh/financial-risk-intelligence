import json

from src.engine.pipeline import run
from src.ingest import make_sample
from src.modules.portfolio import generate
from src.modules.stress_test import (
    load_scenarios,
    read_events,
    run_triggers,
    write_results,
)


def test_end_to_end_synthetic(tmp_path, monkeypatch):
    monkeypatch.setattr(make_sample, "RAW_DIR", tmp_path / "raw")
    make_sample.make(n_news=120, n_tweets=120)
    out = tmp_path / "events.jsonl"
    evs = run(raw_dir=tmp_path / "raw", out_path=out, backend="vader", cache_path=tmp_path / "cache.json")
    assert len(evs) > 100
    lines = out.read_text().splitlines()
    assert len(lines) == len(evs)
    rec = json.loads(lines[0])
    assert {"sentiment", "event", "impact", "entity", "source"} <= set(rec)
    assert "class" in rec["event"] and 1 <= rec["impact"]["score"] <= 10
    assert {e.source.type for e in evs} == {"news", "social"}
    # deterministic
    out2 = tmp_path / "events2.jsonl"
    run(raw_dir=tmp_path / "raw", out_path=out2, backend="vader", cache_path=tmp_path / "cache.json")
    assert out.read_text() == out2.read_text()
    book = generate()
    assert len(book) == 40 and all(e.synthetic for e in book)
    res = run_triggers(read_events(out), book, load_scenarios())
    write_results(res, tmp_path / "stress.jsonl")
    for r in res:
        assert abs(sum(r.by_asset_type.values()) - r.delta) < 1e-6
