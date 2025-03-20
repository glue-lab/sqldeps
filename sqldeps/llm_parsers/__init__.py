from pathlib import Path

from dotenv import load_dotenv

from .base import BaseSQLExtractor
from .deepseek import DeepseekExtractor
from .groq import GroqExtractor
from .openai import OpenaiExtractor

load_dotenv(override=True)

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
