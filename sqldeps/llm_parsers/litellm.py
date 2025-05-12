"""LiteLLM-based SQL parser implementation.

This module provides the LiteLLM-specific implementation of the BaseSQLExtractor
for using various LLM models to extract SQL dependencies.
"""

import os
from pathlib import Path

from litellm import UnsupportedParamsError, completion

from sqldeps.llm_parsers.base import BaseSQLExtractor


class LiteLlmExtractor(BaseSQLExtractor):
    """LiteLLM-based SQL dependency extractor.

    This extractor supports multiple LLM providers through LiteLLM.
    Authentication is handled by LiteLLM, which supports various methods
    depending on the provider (API keys, tokens, or no authentication).

    API keys can be provided as a dictionary mapping environment variable names
    to their values. For example:
        {
            "OPENAI_API_KEY": "sk-...",
            "ANTHROPIC_API_KEY": "sk-...",
        }
    """

    def __init__(
        self,
        model: str = "openai/gpt-4.1",
        params: dict | None = None,
        api_key: dict[str, str] | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        """Initialize LiteLLM extractor.

        Args:
            model: LLM model name to use (supports various providers through LiteLLM)
            params: Additional parameters for the API
            api_key: Optional dictionary mapping environment variable names to
                API key values. For example: {"OPENAI_API_KEY": "sk-..."}
            prompt_path: Path to custom prompt YAML file
        """
        super().__init__(model, params, prompt_path=prompt_path)

        if api_key:
            for env_var, key_value in api_key.items():
                os.environ[env_var] = key_value

    def _query_llm(self, user_prompt: str) -> str:
        """Query the LLM with the generated prompt using LiteLLM.

        Args:
            user_prompt: Generated prompt to send to the LLM

        Returns:
            Response content from the LLM
        """
        messages = [
            {"role": "system", "content": self.prompts["system_prompt"]},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = completion(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                **self.params,
            )
        except UnsupportedParamsError:
            response = completion(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )

        return response.choices[0].message.content
