# Contributing to SQLDeps

Thank you for considering contributing to SQLDeps! This guide explains how to set up your development environment and contribute to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Clone the Repository

```bash
git clone https://github.com/glue-lab/sqldeps.git
cd sqldeps
```

### Install Development Dependencies

SQLDeps uses `uv` as the package manager for development:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

This will install all the required dependencies, including:

- Development tools (`pytest`, `ruff`, etc.)
- Documentation tools (`mkdocs`, etc.)
- Analysis tools (`ipykernel`, `seaborn`, etc.)

### Environment Variables

Create a `.env` file in the project root with your API keys:

```
# LLM API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## Development Workflow

### Code Style

SQLDeps uses Ruff for code formatting and linting:

```bash
# Format code
uv run ruff format .

# Fix linting issues
uv run ruff check . --fix

# Check code style without fixing
make check
```

### Running Tests

```bash
# Run tests without LLM API calls
uv run pytest

# Run tests including LLM API calls (requires API keys)
uv run pytest -m llm

# Run tests with a specific framework
uv run pytest --framework=groq

# Run tests with a specific model
uv run pytest --framework=groq --model=llama-3.3-70b-versatile

# Run tests with a custom prompt
uv run pytest --prompt=configs/prompts/custom.yml
```

### Building Documentation

```bash
# Install documentation dependencies
uv run pip install -r docs/requirements.txt

# Build and serve documentation locally
uv run mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview the documentation.

## Project Structure

- `app/`: Web application using Streamlit
- `configs/`: Configuration files for prompts and databases
- `data/`: Example data files
- `docs/`: Documentation files
- `notebooks/`: Jupyter notebooks for analysis and examples
- `scripts/`: Utility scripts
- `sqldeps/`: Main package source code
    - `database/`: Database connector implementations
    - `llm_parsers/`: LLM integration for SQL parsing
    - `configs/`: Internal configuration files
- `tests/`: Test files

## Adding Features

### Adding a New LLM Provider

1. Create a new file in `sqldeps/llm_parsers/` following the pattern of existing providers
2. Implement the required methods from `BaseSQLExtractor`
3. Add the new provider to `__init__.py` and the `DEFAULTS` dictionary
4. Add tests in `tests/`

### Adding Database Support

1. Create a new file in `sqldeps/database/` following the pattern of existing connectors
2. Implement the required methods from `SQLBaseConnector`
3. Add the new connector to `__init__.py`
4. Add tests in `tests/`

## Pull Request Process

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and add tests
4. Run the tests and linting checks
5. Update documentation if necessary
6. Submit a pull request to the `main` branch

## Versioning

SQLDeps follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backward-compatible manner
- **PATCH** version when making backward-compatible bug fixes

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with the new version and changes
3. Create a new tag with the version number
4. Create a GitHub release
5. Build and publish to PyPI

## Code of Conduct

Please be respectful and inclusive when contributing to SQLDeps. We strive to maintain a welcoming environment for all contributors.

## Questions and Discussion

For questions or discussions, please:

1. Open an issue on GitHub
2. Reach out to the maintainers

## License

By contributing to SQLDeps, you agree that your contributions will be licensed under the project's MIT License.
