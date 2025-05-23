"""Test configuration and fixtures for all tests.

This module provides pytest configuration, custom command-line options,
and fixtures shared across test modules.
"""

from pathlib import Path

import pytest

from sqldeps.llm_parsers import BaseSQLExtractor, create_extractor

# Base paths
TEST_DATA_DIR = Path(__file__).parent / "data"
SQL_DIR = TEST_DATA_DIR / "sql"
EXPECTED_OUTPUT_DIR = TEST_DATA_DIR / "expected_outputs"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom pytest command-line options.

    Args:
        parser: Pytest command-line parser
    """
    parser.addoption(
        "--framework",
        action="store",
        default="litellm",
        help="Specify the framework to use (litellm, openai, groq, deepseek)",
    )
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="Specify the model to use within the selected framework",
    )
    parser.addoption(
        "--prompt",
        action="store",
        default=None,
        help="Specify the path to the prompt yml file to use a custom prompt",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers.

    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line(
        "markers",
        "llm: mark tests that require LLM API calls (typically skipped in CI/CD)",
    )
    config.addinivalue_line(
        "markers", "integration: mark tests that integrate with external services"
    )
    config.addinivalue_line("markers", "slow: mark tests that are slow to execute")


def pytest_collection_modifyitems(
    items: list[pytest.Item], config: pytest.Config
) -> None:
    """Skip slow tests when only llm marker is specified."""
    # Get the value of -m if specified
    markexpr = config.getoption("-m", default="")

    # Check if "llm" is specified but "slow" is not
    if "llm" in markexpr and "slow" not in markexpr:
        skip_marker = pytest.mark.skip(
            reason=(
                "Slow tests are skipped by default. Use -m 'llm and slow' to run them."
            )
        )
        for item in items:
            # If the test has both llm and slow markers, skip it
            if "slow" in item.keywords and "llm" in item.keywords:
                item.add_marker(skip_marker)


@pytest.fixture
def extractor(request: pytest.FixtureRequest) -> BaseSQLExtractor:
    """Create an extractor based on command-line options.

    Args:
        request: Pytest request object

    Returns:
        A configured SQLDeps extractor
    """
    framework = request.config.getoption("--framework")
    model = request.config.getoption("--model")
    prompt = request.config.getoption("--prompt")

    return create_extractor(framework, model, prompt_path=prompt)
