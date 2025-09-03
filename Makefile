.PHONY: test lint format install dev-install clean

# Install dependencies
install:
	poetry install

# Install with dev dependencies
dev-install:
	poetry install --with dev

# Run tests
test:
	poetry run pytest python/test/ -v

# Run tests with coverage
test-cov:
	poetry run pytest python/test/ -v --cov=python/oguild --cov-report=xml

# Run linting
lint:
	poetry run python -m flake8 python/ --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run python -m flake8 python/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run all checks (like CI)
ci: lint test-cov

# Test workflow locally with act
test-workflow:
	act -W .github/workflows/test.yml -j test --env MATRIX_PYTHON_VERSION=3.11

# Clean up
clean:
	rm -rf .pytest_cache
	rm -rf coverage.xml
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
