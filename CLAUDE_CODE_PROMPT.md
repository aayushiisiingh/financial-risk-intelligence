Read CLAUDE.md, docs/SPEC.md, docs/decisions.md and src/schemas.py first. Then build the project in this order, committing after each step with a conventional message and running `pytest` before each commit. Do not ask questions unless blocked; log ambiguities in docs/open-questions.md.

Prerequisite (the user does this manually): raw datasets placed in data/raw_samples/ (one news CSV and one tweets CSV). First inspect their columns and adapt loaders; do not assume column names.

1. src/ingest: loaders for the news and tweet files -> a common SourceItem (text, source type/name, published_at, url); strip @handles; dedup by normalized-text hash; a replay generator ordered by published_at. Restrict to a time range where price data exists.
2. src/ingest/fetch_prices.py: download daily prices for the 15 tickers in config/universe.yaml plus SPY with yfinance, cached to data/prices/*.csv; the pipeline must work from the cache.
3. src/engine/linker.py: cashtag, alias, fuzzy (rapidfuzz) linking per ENG-02.
4. src/engine/sentiment.py: FinBERT (batch inference, CPU, results cached to disk) per ENG-03, plus a VADER baseline function for the eval.
5. src/engine/event_class.py: keyword rules per ENG-04 with a unit test per class.
6. src/engine/impact.py: formula per ENG-05, all numbers from config/impact.yaml, unit tests with hand-computed examples.
7. src/run_pipeline.py: run everything, write data/output/events.jsonl validated against RiskEvent; print counts per source/class.
8. src/modules/portfolio.py: generate and save a deterministic (seeded) SYNTHETIC book of 30-50 exposures to data/portfolio.json mapped to the universe sectors/tickers.
9. src/modules/stress_test.py: valuation per STR-03, trigger and cooldown per STR-02, tests per STR-05 written first with hand-computed values.
10. src/run_stress.py: read events.jsonl, trigger scenarios, write data/output/stress_results.jsonl.
11. src/dashboard/app.py: Streamlit per DSH-01.
12. src/eval: EVL-01 and EVL-02 scripts writing tables/charts to docs/results/. For EVL-01, create a template CSV data/labels/sentiment_sample.csv of 50 sampled feed items with an empty human_label column for the user to fill; the script runs only once labels exist.
13. Update README Section 5 placeholders only with measured results.

Keep it simple and working over fancy. At the end, run `make test` and `make demo` and report anything that does not work.
