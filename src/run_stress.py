from src.modules.portfolio import load
from src.modules.stress_test import (
    load_scenarios,
    read_events,
    run_triggers,
    write_results,
)

if __name__ == "__main__":
    book = load()
    res = run_triggers(read_events(), book, load_scenarios())
    write_results(res)
    print(f"{len(res)} stress tests triggered on a {len(book)}-exposure SYNTHETIC book")
    for r in res[:5]:
        print(f"  {r.stress_id} {r.scenario_id}: {r.portfolio_value_before:,.0f} -> {r.portfolio_value_after:,.0f} ({r.delta_pct:.2%})")
