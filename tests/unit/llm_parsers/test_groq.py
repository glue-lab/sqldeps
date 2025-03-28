"""Unit tests for GroqExtractor."""

from unittest.mock import MagicMock, patch

import pytest

from sqldeps.llm_parsers.groq import GroqExtractor


class TestGroqExtractor:
    """Test suite for GroqExtractor."""

    def test_initialization(self):
        """Test proper initialization with API key."""
        with patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}):
            extractor = GroqExtractor(model="llama-3.3-70b-versatile")

            assert extractor.model == "llama-3.3-70b-versatile"
            assert extractor.framework == "groq"
            assert hasattr(extractor, "client")

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with (
            patch.dict("os.environ", clear=True),
            pytest.raises(ValueError, match="No API key provided"),
        ):
            GroqExtractor(model="llama-3.3-70b-versatile")

    def test_query_llm(self):
        """Test LLM query functionality."""
        with patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}):
            extractor = GroqExtractor(model="llama-3.3-70b-versatile")

            # Mock the Groq client
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
            assert call_args["model"] == "llama-3.3-70b-versatile"
            assert call_args["response_format"] == {"type": "json_object"}
            assert len(call_args["messages"]) == 2
            assert call_args["messages"][0]["role"] == "system"
            assert call_args["messages"][1]["role"] == "user"
