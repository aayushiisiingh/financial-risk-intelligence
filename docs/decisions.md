# Decision log
| # | Decision | Rationale |
|---|---|---|
| D1 | Module B (stress test) is the downstream module. Module A dropped for the one-day build | Case requires at least one; B fits wholesale banking and uses all three engine outputs |
| D2 | US market, 15 S&P 100 stocks | Matches case wording; tweets/news datasets are US-centric |
| D3 | Impact score is formula-based and explainable; components always emitted | Defensible under questioning; no ground truth to train on |
| D4 | Sources: public financial news set (+ GDELT if time) and a public stock-tweet set, replayed | Two distinct source types, deterministic demo |
| D5 | FinBERT sentiment; rule-based event classifier (zero-shot optional) | Fast, benchmarkable, naive baseline built in |
| D6 | Synthetic wholesale book with generic counterparty names mapped to tickers/sectors | Provided retail datasets lack wholesale fields; avoids fake ratings on real names |
| D7 | Replay from cached data only; no live API in the demo path | Reliability |
| D8 | English only | Scope |
| D9 | One event record per (item, entity); null-entity records for sector/macro | Module B needs macro events |
| D10 | JSONL files are the canonical output (no API required) | Case allows "API or file" |
| D11 | Stress trigger has per-scenario cooldown and dedup | Avoid duplicate stress tests from repeated headlines |
| D12 | Impact validated against SPY-adjusted absolute abnormal return, tuned on earlier period, reported on later | Empirical grounding without claiming prediction |
| D13 | Report results as measured, including weak ones | Credibility |
| D14 | Small hand-labelled eval sets from the actual feed | Tests the model on demo data |
