import os
from pathlib import Path

from openai import OpenAI

from sqldeps.llm_parsers.base import BaseSQLExtractor


class OpenaiExtractor(BaseSQLExtractor):
    """OpenAI-based SQL dependency extractor."""

    # Expected environmental variable with the OpenAI key
    ENV_VAR_NAME = "OPENAI_API_KEY"

    def __init__(
        self,
        model: str = "gpt-4o",
        params: dict | None = None,
        api_key: str | None = None,
        prompt_path: Path | None = None,
    ) -> None:
        """Initialize OpenAI extractor."""
        super().__init__(model, params, prompt_path=prompt_path)

        api_key = api_key or os.getenv(self.ENV_VAR_NAME)
        if not api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or set "
                f"{self.ENV_VAR_NAME} environment variable."
            )

        self.client = OpenAI(api_key=api_key)

    def _query_llm(self, user_prompt: str) -> str:
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
