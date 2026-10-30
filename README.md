# Financial Risk Engine: NLP Signals and Event-Driven Stress Testing - S&P Global & Crisil Campus Hackathon

**Candidate Name:** Aayushi Singh
**College Email ID:** [your college email ID]
**College / Campus:** Manipal University
**Demo Video Link:** [YouTube unlisted link]
**Slide Deck Link (if hosted externally):** In repo: docs/presentation.pdf

## 1. Project Overview / Problem Statement & Approach
[2-3 paragraphs. Problem: turning unstructured news and social text into structured financial risk signals that a risk team can act on. Approach: an NLP Risk Engine that ingests two sources, links text to companies, scores sentiment (FinBERT), classifies the event type, and computes an explainable impact score (1-10). Downstream, an event-driven stress-testing module applies configurable shock scenarios to a synthetic wholesale banking portfolio when a high-impact event is detected, and a dashboard shows the before/after impact.]

## 2. Architecture & Tech Stack
![Architecture](docs/architecture.png)
- Python 3.11, Pydantic (data contracts), Hugging Face transformers (FinBERT), pandas, scikit-learn, yfinance (cached), Streamlit + Plotly.
- Data flow: sources -> dedup/handle stripping -> entity linking -> sentiment -> event class -> impact -> events.jsonl -> scenario trigger -> stress engine -> stress_results.jsonl -> dashboard.

## 3. Dataset Used
- [List each dataset with source URL and license: news set, tweet set, optional GDELT.]
- Prices: yfinance historical daily, cached in data/prices.
- Portfolio: fully SYNTHETIC wholesale book (loans, bonds, swaps, FX forwards) with generic counterparty names. Ratings, PDs and exposures are fictional and not real credit views.
- Assumptions: replayed historical feed stands in for real time; shock magnitudes are illustrative scenario assumptions; English text only.
- No S&P Global or Crisil data was used.

## 4. Quickstart & Installation
Runtime: Python 3.11 on [your OS]
```bash
git clone <your-repo-url>
cd manipal-aayushi-singh-hackathon
pip install -r requirements.txt
make demo    # runs the engine, the stress test, then launches the dashboard (offline, cached data)
make test    # unit tests
```
First run downloads the FinBERT model (a few hundred MB). No API keys needed for the demo.

## 5. Key Results & Domain Impact
- [Sentiment: FinBERT vs VADER macro-F1 on a hand-labelled sample.]
- [Impact score vs next-day absolute abnormal return, by bucket.]
- [Stress test: example before/after portfolio value for each scenario.]
- Why it matters: [early-warning signals for wholesale banking risk teams, traceable scores, scenario-based what-ifs.]

## Limitations
Research prototype, not investment advice. Heuristic impact score, illustrative shocks, English only, replayed historical data, susceptible to sarcasm and coordinated posting.

## AI Usage
Claude (Anthropic) was used for planning, code assistance and review. Design decisions are documented in docs/decisions.md.
