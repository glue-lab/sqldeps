# Contributing to SQLDeps

Thank you for considering contributing to SQLDeps! This guide explains how to set up your development environment and contribute to the project.

## Questions and Discussion

For questions or discussions, please check [SQLDeps Discussions](https://github.com/glue-lab/sqldeps/discussions) or reach out to the maintainers directly.

## Development Setup

### Prerequisites

- [Git](https://git-scm.com/)
- [UV](https://docs.astral.sh/uv/)

### Clone the Repository

```bash
git clone https://github.com/glue-lab/sqldeps.git
cd sqldeps
```

### Install Development Dependencies

SQLDeps uses [`uv`](https://github.com/astral-sh/uv) as the package manager for development.

After installing UV, run:

```bash
uv sync
```

This will create a virtual environment with the correct Python version and all the required dependencies, including:

- Core dependencies
- Development tools (`pytest`, `ruff`, etc.)
- Documentation tools (`mkdocs`, etc.)

### Environment Variables

Create a `.env` file in the project root with your API keys:

```
# LLM API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

For instance, [Groq](https://console.groq.com/keys) offers free tokens without requiring payment details, making it ideal for contributions.

## Development Workflow

### Code Style

SQLDeps uses Ruff for code formatting and linting:

```bash
# Format code
uv run ruff format .

# Fix linting issues
uv run ruff check . --fix
```

Alternatively, you can easily check and apply formatting and linting with `make`:

```bash
# Check code style without fixing
make check

# Apply fixes
make fix
```

### Running Tests

The test suite is set up with markers to allow selective testing:

```bash
# Run all tests except those marked as 'llm' or 'integration'
# This is the default when running pytest without arguments
uv run pytest

# Run tests with a specific marker
uv run pytest -m llm  # Run LLM-dependent tests (requires API keys)
uv run pytest -m integration  # Run integration tests (requires database)

# Run tests with a specific framework
uv run pytest --framework=groq

# Run specific test files
uv run pytest tests/unit/test_models.py

# Run with coverage report
uv run pytest --cov=sqldeps
```

Note that by default tests marked with `llm` and `integration` are skipped to avoid requiring external dependencies during CI/CD. These tests require valid API keys and/or database connections.

### Building Documentation

```bash
# Build and serve documentation locally
uv run mkdocs serve
```

This will start a local server at `http://127.0.0.1:8000` where you can preview the documentation.

## Project Structure

Here's the simplified project structure:

```
sqldeps/
├── .github/              # GitHub configuration files
├── configs/              # External configuration files for experiments
├── docs/                 # Documentation files
├── sqldeps/              # Main package source code
│   ├── app/              # Streamlit web application
│   ├── database/         # Database connector implementations
│   ├── llm_parsers/      # LLM integration for SQL parsing
│   └── ...               # Other core modules
└── tests/                # Test suite
```

## Adding Features

### Adding a New LLM Provider

1. Create a new file in `sqldeps/llm_parsers/` following the pattern of existing providers
2. Implement the required methods from `BaseSQLExtractor`
3. Add the new provider to `__init__.py` and the `DEFAULTS` dictionary
4. Add tests in `tests/` (both unit and functional tests)

### Adding Database Support

1. Create a new file in `sqldeps/database/` following the pattern of existing connectors
2. Implement the required methods from `SQLBaseConnector`
3. Add the new connector to `__init__.py`
4. Add tests in `tests/` (both unit and integration tests)

## Pull Request Process

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and add tests
4. Run the tests and linting checks
5. Update documentation if necessary
6. Submit a pull request to the `main` branch

## Package Versioning

SQLDeps follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backward-compatible manner
- **PATCH** version when making backward-compatible bug fixes

## Code of Conduct

Please be respectful and inclusive when contributing to SQLDeps. We strive to maintain a welcoming environment for all contributors.

## License

By contributing to SQLDeps, you agree that your contributions will be licensed under the project's MIT License.
