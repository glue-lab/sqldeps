.PHONY: fix 
fix:
	uv run ruff format .
	uv run ruff check . --fix

.PHONY: check
check:
	-uv run ruff format . --check
	-uv run ruff check .

.PHONY: clean
clean:
	# Remove Python cache directories
	find . -type d \( \
		-name "__pycache__" -o \
		-name "*.egg-info" -o \
		-name ".eggs" -o \
		-name ".ipynb_checkpoints" \
	\) -exec rm -rf {} +

	# Remove compiled Python files
	find . -name "*.pyc" -delete

	# Remove build, test, and cache directories
	rm -rf dist build htmlcov .pytest_cache .ruff_cache .sqldeps_cache .mypy_cache .tox 2>/dev/null || true
