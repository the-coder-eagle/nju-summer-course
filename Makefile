test:
	python -m pytest -q

run:
	uvicorn web.app:app --reload --port 8000

lint:
	ruff check . && mypy src
