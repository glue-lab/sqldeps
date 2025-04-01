"""Unit tests for command-line interface.

This module tests the functionality of the CLI commands and related functions.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sqldeps.cli import app, extract, extract_dependencies, save_output
from sqldeps.models import SQLProfile


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner for testing.

    Returns:
        CliRunner: A Typer CLI test runner
    """
    return CliRunner()


@pytest.fixture
def mock_sql_profile() -> SQLProfile:
    """Create a mock SQLProfile for testing.

    Returns:
        SQLProfile: A sample SQLProfile for testing
    """
    return SQLProfile(
        dependencies={"users": ["id", "name"]}, outputs={"reports": ["date", "total"]}
    )


class TestCLI:
    """Test suite for command-line interface."""

    def test_extract_dependencies(self, mock_sql_profile: SQLProfile) -> None:
        """Test extraction of dependencies."""
        # Mock the extractor
        mock_extractor = MagicMock()
        mock_extractor.extract_from_file.return_value = mock_sql_profile
        mock_extractor.extract_from_folder.return_value = {"file.sql": mock_sql_profile}

        # Test file extraction
        with patch("pathlib.Path.is_file", return_value=True):
            result = extract_dependencies(mock_extractor, Path("file.sql"), False)
            assert result == mock_sql_profile
            mock_extractor.extract_from_file.assert_called_once()

        # Test folder extraction
        with patch("pathlib.Path.is_file", return_value=False):
            result = extract_dependencies(mock_extractor, Path("folder"), True)
            assert result == {"file.sql": mock_sql_profile}
            mock_extractor.extract_from_folder.assert_called_once()

    def test_save_output(self, mock_sql_profile: SQLProfile, tmp_path: Path) -> None:
        """Test saving output to different formats."""
        # Test JSON output
        json_path = tmp_path / "output.json"
        save_output(mock_sql_profile, json_path)
        assert json_path.exists()

        # Test CSV output
        csv_path = tmp_path / "output.csv"
        save_output(mock_sql_profile, csv_path)
        assert csv_path.exists()

        # Test CSV output with schema match
        df_mock = MagicMock()
        df_mock.to_csv = MagicMock()
        save_output(df_mock, csv_path, is_schema_match=True)
        df_mock.to_csv.assert_called_once()

    def test_cli_command(self, runner: CliRunner, mock_sql_profile: SQLProfile) -> None:
        """Test the CLI command execution using isolated components."""
        with (
            patch("sqldeps.cli.create_extractor") as mock_create_extractor,
            patch("sqldeps.cli.extract_dependencies") as mock_extract,
            patch("sqldeps.cli.save_output") as mock_save,
        ):
            # Setup mocks
            mock_extractor = MagicMock()
            mock_create_extractor.return_value = mock_extractor
            mock_extract.return_value = mock_sql_profile

            # Use the extract function directly instead of 'main'
            extract(
                fpath=Path("file.sql"),
                framework="groq",
                model=None,
                prompt=None,
                recursive=False,
                db_match_schema=False,
                db_target_schemas="public",
                db_credentials=None,
                output=Path("dependencies.json"),
            )

            # Verify function calls
            mock_create_extractor.assert_called_once()
            mock_extract.assert_called_once()
            mock_save.assert_called_once()

    def test_cli_error_handling(self) -> None:
        """Test error handling in CLI using mock directly."""
        with patch("sqldeps.cli.create_extractor") as mock_create_extractor:
            # Make the extractor creation raise an exception
            mock_create_extractor.side_effect = ValueError("Test error")

            # Call the extract function directly and catch the exception
            from typer import Exit

            with pytest.raises(Exit) as excinfo:
                extract(
                    fpath=Path("file.sql"),
                    framework="groq",
                    model=None,
                    prompt=None,
                    recursive=False,
                    db_match_schema=False,
                    db_target_schemas="public",
                    db_credentials=None,
                    output=Path("dependencies.json"),
                )

            # Verify the exit code is 1
            assert excinfo.value.exit_code == 1

    def test_cli_database_validation(self, mock_sql_profile: SQLProfile) -> None:
        """Test database validation logic directly."""
        with (
            patch("sqldeps.cli.create_extractor") as mock_create_extractor,
            patch("sqldeps.cli.extract_dependencies") as mock_extract,
            patch("sqldeps.cli.match_dependencies_against_schema") as mock_match,
            patch("sqldeps.cli.save_output"),
            patch("builtins.open", MagicMock()),
            patch("yaml.safe_load", return_value={"database": {}}),
        ):
            # Setup mocks
            mock_extractor = MagicMock()
            mock_create_extractor.return_value = mock_extractor
            mock_extract.return_value = mock_sql_profile
            mock_match.return_value = MagicMock()  # Mock DataFrame result

            # Call the extract function directly
            extract(
                fpath=Path("file.sql"),
                framework="groq",
                model=None,
                prompt=None,
                recursive=False,
                db_match_schema=True,
                db_target_schemas="public",
                db_credentials=Path("config.yml"),
                output=Path("dependencies.json"),
            )

            # Verify function calls
            mock_match.assert_called_once()

    def test_app_version(self, runner: CliRunner) -> None:
        """Test CLI app version command."""
        # The version command is a safer option to test CLI integration
        result = runner.invoke(app, ["--version"])

        # Version command should not produce an error
        assert result.exit_code == 0
        assert "SQLDeps version:" in result.output

    def test_app_command(self) -> None:
        """Test the app command functionality."""
        with (
            patch("sqldeps.cli.subprocess.run") as mock_run,
            patch("sqldeps.cli.Path.exists", return_value=True),
        ):
            from sqldeps.cli import app_main

            app_main()
            mock_run.assert_called_once()

    def test_cache_clear_command(self) -> None:
        """Test the cache clear command."""
        with patch("sqldeps.cli.cleanup_cache", return_value=True) as mock_cleanup:
            from sqldeps.cli import cache_clear

            cache_clear()
            mock_cleanup.assert_called_once()
