def pytest_addoption(parser) -> None:
    """Register custom pytest command-line options"""
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
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "llm: mark tests that require LLM API calls (typically skipped in CI/CD)",
    )
