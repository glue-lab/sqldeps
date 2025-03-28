"""Test configuration and fixtures for all tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sqldeps.llm_parsers import create_extractor
from sqldeps.models import SQLProfile

# Base paths
TEST_DATA_DIR = Path(__file__).parent / "data"
SQL_DIR = TEST_DATA_DIR / "sql"
EXPECTED_OUTPUT_DIR = TEST_DATA_DIR / "expected_outputs"


def pytest_addoption(parser):
    """Register custom pytest command-line options."""
    parser.addoption(
        "--framework",
        action="store",
        default="groq",
        help="Specify the framework to use (openai, groq, deepseek)",
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


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "llm: mark tests that require LLM API calls (typically skipped in CI/CD)",
    )
    config.addinivalue_line(
        "markers", "integration: mark tests that integrate with external services"
    )
    config.addinivalue_line("markers", "slow: mark tests that are slow to execute")


@pytest.fixture
def extractor(request):
    """Create an extractor based on command-line options."""
    framework = request.config.getoption("--framework")
    model = request.config.getoption("--model")
    prompt = request.config.getoption("--prompt")

    return create_extractor(framework, model, prompt_path=prompt)


@pytest.fixture
def mock_extractor():
    """Create a mocked extractor for tests."""
    mock = MagicMock()
    mock.extract_from_query.return_value = SQLProfile(
        dependencies={"test_table": ["column1"]}, outputs={"output_table": ["column2"]}
    )
    return mock
