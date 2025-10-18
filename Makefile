# Makefile

.PHONY: test lint

# Run all tests with proper PYTHONPATH
test:
	PYTHONPATH=. pytest test

# Run tests with coverage (optional)
coverage:
	PYTHONPATH=. pytest --cov=core test

# Run linter (if using one)
lint:
	ruff check .