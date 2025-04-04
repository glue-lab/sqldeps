"""LLM-based SQL parsers for dependency extraction.

This package provides integrations with various LLM providers for extracting
SQL dependencies, with a common interface and factory function.
"""

from pathlib import Path

from dotenv import load_dotenv

from .base import BaseSQLExtractor
from .deepseek import DeepseekExtractor
from .groq import GroqExtractor
from .openai import OpenaiExtractor

load_dotenv()

DEFAULTS = {
    "groq": {"class": GroqExtractor, "model": "llama-3.3-70b-versatile"},
    "openai": {"class": OpenaiExtractor, "model": "gpt-4o"},
    "deepseek": {"class": DeepseekExtractor, "model": "deepseek-chat"},
}


def create_extractor(
    framework: str = "groq",
    model: str | None = None,
    params: dict | None = None,
    prompt_path: Path | None = None,
) -> BaseSQLExtractor:
    """Create an appropriate SQL extractor based on the specified framework.

    Args:
        framework: The LLM framework to use ("groq", "openai", or "deepseek")
        model: The model name within the selected framework (uses default if None)
        params: Additional parameters to pass to the LLM API
        prompt_path: Path to a custom prompt YAML file

    Returns:
        An instance of the appropriate SQL extractor

    Raises:
        ValueError: If an unsupported framework is specified
    """
    framework = framework.lower()
    if framework not in DEFAULTS:
        raise ValueError(
            f"Unsupported framework: {framework}. "
            f"Must be one of: {', '.join(DEFAULTS.keys())}"
        )

    config = DEFAULTS[framework]
    extractor_class = config["class"]
    model_name = model or config["model"]

    return extractor_class(model=model_name, params=params, prompt_path=prompt_path)


__all__ = ["DeepseekExtractor", "GroqExtractor", "OpenaiExtractor", "create_extractor"]
