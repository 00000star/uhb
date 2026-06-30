.PHONY: install install-dev test lint clean benchmark dashboard

# Install all packages in development mode
install:
	cd uhb-core && pip install -e .
	cd uhb-benchmark && pip install -e .
	cd uhb-personality && pip install -e .
	cd uhb-environment && pip install -e .
	cd uhb-memory && pip install -e .
	cd uhb-tools && pip install -e .
	cd uhb-evolution && pip install -e .
	cd uhb-compiler && pip install -e .
	cd uhb-systems && pip install -e .
	cd uhb-community && pip install -e .
	cd uhb-dashboard && pip install -e .

install-dev: install
	cd uhb-core && pip install -e ".[dev]"
	cd uhb-benchmark && pip install -e ".[dev]"
	cd uhb-evolution && pip install -e ".[dev]"

test:
	cd uhb-core && python -m pytest tests/ -v
	cd uhb-benchmark && python -m pytest tests/ -v
	cd uhb-evolution && python -m pytest tests/ -v

benchmark:
	python -m uhb.benchmark.cli profile anthropic/claude-sonnet-4-6 --seeds 1

dashboard:
	streamlit run uhb-dashboard/dashboard/app.py --server.port 8501

lint:
	ruff check uhb-*/ --fix

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null || true
	rm -rf data/cache/* data/results/*
