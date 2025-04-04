"""OpenAI-based SQL parser implementation.

This module provides the OpenAI-specific implementation of the BaseSQLExtractor
for using OpenAI's models to extract SQL dependencies.
"""

import os
from pathlib import Path

from openai import OpenAI

from sqldeps.llm_parsers.base import BaseSQLExtractor


class OpenaiExtractor(BaseSQLExtractor):
    """OpenAI-based SQL dependency extractor.

    Attributes:
        ENV_VAR_NAME: Environment variable name for the API key
        client: OpenAI client instance
    """

    # Expected environmental variable with the OpenAI key
    ENV_VAR_NAME = "OPENAI_API_KEY"

    def __init__(
        self,
        model: str = "gpt-4o",
        params: dict | None = None,
        api_key: str | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        """Initialize OpenAI extractor.

        Args:
            model: OpenAI model name to use
            params: Additional parameters for the API
            api_key: OpenAI API key (defaults to environment variable)
            prompt_path: Path to custom prompt YAML file

        Raises:
            ValueError: If API key is not provided
        """
        super().__init__(model, params, prompt_path=prompt_path)

        api_key = api_key or os.getenv(self.ENV_VAR_NAME)
        if not api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or set "
                f"{self.ENV_VAR_NAME} environment variable."
            )

        self.client = OpenAI(api_key=api_key)

    def _query_llm(self, user_prompt: str) -> str:
        """Query the OpenAI LLM with the generated prompt.

        Args:
            user_prompt: Generated prompt to send to OpenAI

        Returns:
            Response content from OpenAI
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
