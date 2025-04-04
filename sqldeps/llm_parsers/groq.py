"""Groq-based SQL parser implementation.

This module provides the Groq-specific implementation of the BaseSQLExtractor
for using Groq's models to extract SQL dependencies.
"""

import os
from pathlib import Path

from groq import Groq

from sqldeps.llm_parsers.base import BaseSQLExtractor


class GroqExtractor(BaseSQLExtractor):
    """Groq-based SQL dependency extractor.

    Attributes:
        ENV_VAR_NAME: Environment variable name for the API key
        client: Groq client instance
    """

    ENV_VAR_NAME = "GROQ_API_KEY"

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        params: dict | None = None,
        api_key: str | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        """Initialize Groq extractor."""
        super().__init__(model, params, prompt_path=prompt_path)

        api_key = api_key or os.getenv(self.ENV_VAR_NAME)
        if not api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or set "
                f"{self.ENV_VAR_NAME} environment variable."
            )

        self.client = Groq(api_key=api_key)

    def _query_llm(self, user_prompt: str) -> str:
        """Query the Groq LLM with the generated prompt.

        Args:
            user_prompt: Generated prompt to send to Groq

        Returns:
            Response content from Groq
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompts["system_prompt"]},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            **self.params,
        )

        return response.choices[0].message.content
