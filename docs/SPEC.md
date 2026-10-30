# SPEC (condensed). IDs are referenced by tests and commits.

## Engine
- ENG-01 Ingest >= 2 sources (news, social) into a common SourceItem; strip user handles; dedup by normalized-text hash.
- ENG-02 Entity linking: cashtag, then alias (config/universe.yaml), then fuzzy (rapidfuzz, threshold 90). No match => ticker null (sector/macro).
- ENG-03 Sentiment: ProsusAI/finbert. score = P(pos) - P(neg) in [-1,1]; label via thresholds in config/impact.yaml.
- ENG-04 Event class: keyword rules over the 9-class enum (src/schemas.py EventClass); fallback Other. Zero-shot optional.
- ENG-05 Impact: clip(round(1 + 9*S*R*(0.4*|sent| + 0.3*cred + 0.3*novelty)), 1, 10); always emit components. All numbers from config/impact.yaml.
- ENG-06 Output data/output/events.jsonl, every line validates as RiskEvent. Deterministic for fixed input.

## Module B
- STR-01 Portfolio data/portfolio.json: 30-50 SYNTHETIC exposures (loan, bond, irs, fx_forward), generic counterparty names, linked_ticker/sector, mapped to the universe.
- STR-02 Trigger: event class and impact >= min_impact from config/scenarios.yaml; cooldown per scenario.
- STR-03 Valuation (rates/spreads in decimal = bps/10000):
  - bond: dP = P * (-D_mod * d_rate - D_spread * d_spread)
  - loan: dEL = EAD * LGD * (min(PD*pd_multiplier, 1) - PD), reported as expected_loss_change
  - irs: dMTM = +/- DV01 * rate_bps (pay_fixed gains when rates rise)
  - fx_forward: dMTM = delta_notional * fx_pct
  - sector overlays modify the equity shock; if no equity-like exposure exists they are reported but unused.
- STR-04 Output data/output/stress_results.jsonl as StressResult; sum(by_asset_type) == delta; sum(by_exposure) == delta.
- STR-05 Tests with hand-computed values: zero shock => zero change; bond duration 4, +100bp => -4%; linearity; trigger/cooldown.

## Dashboard
- DSH-01 Streamlit: event feed (filter by ticker/class/impact), impact distribution, stress before/after bar, by-asset-type and by-sector breakdown, SYNTHETIC banner and "not investment advice" note.

## Evaluation (minimal, one-day)
- EVL-01 Sentiment: FinBERT vs VADER macro-F1 on ~50 hand-labelled items from the feed.
- EVL-02 Impact buckets (1-3, 4-6, 7-10) vs mean absolute abnormal return vs SPY, if prices are cached. Report as measured.

## Non-goals today
Module A, FastAPI, live NewsAPI, ablations, sensitivity study, event-class F1 study (list as next steps).
