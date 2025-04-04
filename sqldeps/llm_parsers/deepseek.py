"""DeepSeek-based SQL parser implementation.

This module provides the DeepSeek-specific implementation of the BaseSQLExtractor
for using DeepSeek's models to extract SQL dependencies.
"""

import os
from pathlib import Path

from openai import OpenAI

from sqldeps.llm_parsers.base import BaseSQLExtractor


class DeepseekExtractor(BaseSQLExtractor):
    """DeepSeek-based SQL dependency extractor.

    Attributes:
        ENV_VAR_NAME: Environment variable name for the API key
        client: OpenAI client instance configured for DeepSeek API
    """

    # Expected environmental variable with the DeepSeek key
    ENV_VAR_NAME = "DEEPSEEK_API_KEY"

    def __init__(
        self,
        model: str = "deepseek-chat",
        params: dict | None = None,
        api_key: str | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        """Initialize DeepSeek extractor.

        Args:
            model: DeepSeek model name to use
            params: Additional parameters for the API
            api_key: DeepSeek API key (defaults to environment variable)
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

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def _query_llm(self, user_prompt: str) -> str:
        """Query the DeepSeek LLM with the generated prompt.

        Args:
            user_prompt: Generated prompt to send to DeepSeek

        Returns:
            Response content from DeepSeek
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompts["system_prompt"]},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            stream=False,
            **self.params,
        )

        return response.choices[0].message.content
