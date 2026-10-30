# Project: Financial Risk Engine (S&P Global & Crisil Campus Hackathon, individual)

## Source of truth
- docs/SPEC.md and docs/decisions.md. If code and spec disagree, stop and ask.
- Contracts live in src/schemas.py. Do not change a schema without updating SPEC.md and tests.

## Rules
- Python 3.11, type hints, ruff clean, pytest green before every commit.
- No real S&P/Crisil data. Public or synthetic data only. Synthetic data must be labelled SYNTHETIC.
- Never commit secrets or large data. Samples only (<5 MB each); download scripts for the rest.
- All tunable numbers (weights, thresholds, shocks) live in config/*.yaml, not in code.
- Impact score stays formula-based and explainable; always emit components.
- Strip user handles from social text at ingestion.
- The demo path must run offline from cached data. Live calls are optional and fail gracefully.
- Seed everything; same input gives the same output.
- Do not claim results you have not measured. Eval scripts write to docs/results/.

## Workflow
- Small commits, conventional messages (feat:, test:, fix:, docs:).
- Write the tests first for stress-test math using hand-computed values from SPEC.
- After each milestone: run `make test`, summarize, then continue. Ask only if truly blocked.
- Ambiguities go to docs/open-questions.md; do not guess silently.
