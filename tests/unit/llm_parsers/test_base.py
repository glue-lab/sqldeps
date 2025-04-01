"""Unit tests for BaseSQLExtractor.

This module contains tests for the common functionality provided by the
BaseSQLExtractor abstract base class.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from sqldeps.llm_parsers import BaseSQLExtractor
from sqldeps.models import SQLProfile


class MockSQLExtractor(BaseSQLExtractor):
    """Test implementation of BaseSQLExtractor for unit testing.

    This class provides a concrete implementation of the abstract BaseSQLExtractor
    that can be used in tests with mocked LLM responses.
    """

    def __init__(
        self,
        model: str = "test-model",
        params: dict | None = None,
        prompt_path: str | None = None,
    ) -> None:
        """Initialize the mock extractor.

        Args:
            model: Model name
            params: Additional parameters
            prompt_path: Path to custom prompt file
        """
        super().__init__(model, params, prompt_path)

    def _query_llm(self, prompt: str) -> str:
        """Implement the abstract method from the parent class.

        In actual tests, this method will typically be mocked.

        Args:
            prompt: Prompt to send to the LLM

        Returns:
            Empty string (will be mocked in tests)
        """
        return ""


@pytest.fixture
def mock_extractor() -> MockSQLExtractor:
    """Provide a mock SQL extractor for tests.

    Returns:
        MockSQLExtractor: A concrete implementation of BaseSQLExtractor
    """
    return MockSQLExtractor()


@pytest.fixture
def mock_sql_response() -> callable:
    """Create a standard SQL dependency response.

    Returns:
        function: A function that creates JSON responses with given dependencies/outputs
    """

    def _create_response(
        dependencies: dict | None = None, outputs: dict | None = None
    ) -> str:
        return json.dumps(
            {"dependencies": dependencies or {}, "outputs": outputs or {}}
        )

    return _create_response


class TestBaseSQLExtractor:
    """Test suite for BaseSQLExtractor."""

    def test_initialization(self, mock_extractor: MockSQLExtractor) -> None:
        """Test proper initialization of BaseSQLExtractor."""
        assert mock_extractor.model == "test-model"
        assert mock_extractor.framework == "mocksql"
        assert mock_extractor.params == {"temperature": 0}

    def test_extract_from_query(
        self, mock_extractor: MockSQLExtractor, mock_sql_response: callable
    ) -> None:
        """Test extraction from a SQL query."""
        response = mock_sql_response(
            dependencies={"table1": ["col1", "col2"]}, outputs={"table2": ["col3"]}
        )

        mock_extractor._query_llm = MagicMock(return_value=response)
        result = mock_extractor.extract_from_query("SELECT col1, col2 FROM table1")

        assert isinstance(result, SQLProfile)
        assert result.dependencies == {"table1": ["col1", "col2"]}
        assert result.outputs == {"table2": ["col3"]}
        mock_extractor._query_llm.assert_called_once()

    def test_extract_from_file(
        self, mock_extractor: MockSQLExtractor, mock_sql_response: callable
    ) -> None:
        """Test extraction from a SQL file."""
        mock_sql = "SELECT * FROM users"
        response = mock_sql_response(dependencies={"users": ["*"]})

        mock_extractor._query_llm = MagicMock(return_value=response)

        with (
            patch("builtins.open", mock_open(read_data=mock_sql)),
            patch.object(Path, "exists", return_value=True),
        ):
            result = mock_extractor.extract_from_file("fake_path.sql")

        assert result.dependencies == {"users": ["*"]}
        assert result.outputs == {}

    def test_file_not_found(self, mock_extractor: MockSQLExtractor) -> None:
        """Test handling of file not found."""
        with (
            patch.object(Path, "exists", return_value=False),
            pytest.raises(FileNotFoundError),
        ):
            mock_extractor.extract_from_file("nonexistent.sql")

    def test_extract_from_folder(self, mock_extractor: MockSQLExtractor) -> None:
        """Test extraction from a folder."""
        with patch("sqldeps.llm_parsers.base.find_sql_files") as mock_find:
            # Setup mock files
            mock_files = [Path("file1.sql"), Path("file2.sql")]
            mock_find.return_value = mock_files

            # Mock file extraction
            mock_extractor.extract_from_file = MagicMock(
                return_value=SQLProfile(dependencies={"table1": ["col1"]}, outputs={})
            )

            # Explicitly disable cache usage
            result = mock_extractor.extract_from_folder(
                "test_folder", recursive=True, n_workers=1, use_cache=False
            )

            # Verify results
            assert len(result) == len(mock_files)
            assert mock_extractor.extract_from_file.call_count == len(mock_files)

    @pytest.mark.parametrize(
        "response,error_pattern",
        [
            ("Invalid JSON", "Failed to decode JSON"),
            ('{"only_dependencies": {}}', "Missing required keys"),
        ],
    )
    def test_process_response_errors(
        self, mock_extractor: MockSQLExtractor, response: str, error_pattern: str
    ) -> None:
        """Test handling of different error conditions.

        Args:
            mock_extractor: Mock extractor fixture
            response: Response string to process
            error_pattern: Expected error message pattern
        """
        with pytest.raises(ValueError, match=error_pattern):
            mock_extractor._process_response(response)

    def test_load_prompts_default(self, mock_extractor: MockSQLExtractor) -> None:
        """Test loading default prompts."""
        # Define a dict that mimics parsed YAML
        mock_yaml_data = {
            "system_prompt": "test system prompt",
            "user_prompt": "test user prompt",
        }

        # Directly patch yaml.safe_load to return our mock data
        with patch("yaml.safe_load", return_value=mock_yaml_data):
            # Create a new extractor to trigger _load_prompts
            extractor = MockSQLExtractor()

            # Verify the prompts were loaded correctly
            assert extractor.prompts == mock_yaml_data
            assert extractor.prompts["system_prompt"] == "test system prompt"
            assert extractor.prompts["user_prompt"] == "test user prompt"

    def test_normalize_extensions(self) -> None:
        """Test normalization of file extensions."""
        result = MockSQLExtractor._normalize_extensions({".SQL", "sql", ".Sql"})
        assert result == {"sql"}

        result = MockSQLExtractor._normalize_extensions(None)
        assert result == {"sql"}  # Default extension
