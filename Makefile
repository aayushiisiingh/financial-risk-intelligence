PY=python
setup:
	$(PY) -m pip install -r requirements.txt
data:
	$(PY) -m src.ingest.fetch_prices
pipeline:
	$(PY) -m src.run_pipeline
stress:
	$(PY) -m src.run_stress
eval:
	$(PY) -m src.eval.run_all
demo: pipeline stress
	streamlit run src/dashboard/app.py
test:
	pytest -q
lint:
	ruff check src tests
