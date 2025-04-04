"""Unit tests for sqldeps.llm_parsers.__init__.

This module tests the factory function and other initialization
logic of the llm_parsers package.
"""

import pytest

from sqldeps.llm_parsers import create_extractor


class TestLLMParsersInit:
    """Test suite for sqldeps.llm_parsers.__init__."""

    def test_create_extractor_invalid_framework(self) -> None:
        """Test creating an extractor with invalid framework."""
        # No need to patch anything for this test
        with pytest.raises(ValueError, match="Unsupported framework"):
            create_extractor(framework="invalid_framework")
