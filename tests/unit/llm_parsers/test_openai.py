"""Unit tests for OpenaiExtractor.

This module tests the OpenAI-specific LLM implementation.
"""

from unittest.mock import MagicMock, patch

import pytest

from sqldeps.llm_parsers.openai import OpenaiExtractor


class TestOpenaiExtractor:
    """Test suite for OpenaiExtractor."""

    def test_initialization(self) -> None:
        """Test proper initialization with API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "fake-key"}):
            extractor = OpenaiExtractor(model="gpt-4o")

            assert extractor.model == "gpt-4o"
            assert extractor.framework == "openai"
            assert hasattr(extractor, "client")

    def test_initialization_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        with (
            patch.dict("os.environ", clear=True),
            pytest.raises(ValueError, match="No API key provided"),
        ):
            OpenaiExtractor(model="gpt-4o")

    def test_query_llm(self) -> None:
        """Test LLM query functionality."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "fake-key"}):
            extractor = OpenaiExtractor(model="gpt-4o")

            # Mock the OpenAI client
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[
                0
            ].message.content = '{"dependencies": {}, "outputs": {}}'

            extractor.client = MagicMock()
            extractor.client.chat.completions.create.return_value = mock_response

            # Test the query
            result = extractor._query_llm("SELECT * FROM test")

            # Verify the response and method calls
            assert result == '{"dependencies": {}, "outputs": {}}'
            extractor.client.chat.completions.create.assert_called_once()

            # Verify correct parameters were passed
            call_args = extractor.client.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-4o"
            assert call_args["response_format"] == {"type": "json_object"}
            assert len(call_args["messages"]) == 2
            assert call_args["messages"][0]["role"] == "system"
            assert call_args["messages"][1]["role"] == "user"
