"""Unit tests for PostgreSQLConnector.

This module contains unit tests for the PostgreSQL connector functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
import yaml

from sqldeps.database.postgresql import PostgreSQLConnector


class TestPostgreSQLConnector:
    """Test suite for PostgreSQLConnector."""

    def test_initialization_with_params(self) -> None:
        """Test initialization with direct parameters."""
        # Mock both create_engine and inspect
        with (
            patch("sqldeps.database.postgresql.create_engine") as mock_engine,
            patch("sqldeps.database.postgresql.inspect") as mock_inspect,
        ):
            # Set up the mock inspector that will be returned
            mock_inspector = MagicMock()
            mock_inspect.return_value = mock_inspector

            connector = PostgreSQLConnector(
                host="localhost",
                port=5432,
                database="testdb",
                username="user",
                password="pass",
            )

            # Verify engine was created
            mock_engine.assert_called_once()
            # Verify inspector was created
            mock_inspect.assert_called_once()
            assert connector.inspector == mock_inspector

    def test_initialization_missing_params(self) -> None:
        """Test initialization fails with missing parameters."""
        with (
            pytest.raises(ValueError, match="Missing required database parameters"),
            patch("os.getenv", return_value=None),
        ):
            PostgreSQLConnector(
                host=None, database="testdb", username="user", password="pass"
            )

    def test_initialization_with_config_file(self) -> None:
        """Test initialization with YAML config file."""
        config_data = {
            "database": {
                "host": "dbhost",
                "port": 5432,
                "database": "configdb",
                "username": "configuser",
                "password": "configpass",
            }
        }

        with (
            patch("builtins.open", mock_open(read_data=yaml.dump(config_data))),
            patch("sqldeps.database.postgresql.create_engine") as mock_engine,
            patch("sqldeps.database.postgresql.inspect") as mock_inspect,
            patch.object(Path, "exists", return_value=True),
        ):
            # Set up the mock inspector
            mock_inspector = MagicMock()
            mock_inspect.return_value = mock_inspector

            PostgreSQLConnector(config_path=Path("config.yml"))

            # Verify engine was created with correct parameters
            mock_engine.assert_called_once()
            # Verify connection string contains expected values
            conn_string = mock_engine.call_args[0][0]
            assert "dbhost" in conn_string
            assert "configdb" in conn_string
            assert "configuser" in conn_string

    def test_get_schema(self) -> None:
        """Test schema retrieval functionality."""
        with (
            patch("sqldeps.database.postgresql.create_engine"),
            patch("sqldeps.database.postgresql.inspect") as mock_inspect,
        ):
            # Create mock inspector with appropriate return values
            mock_inspector = MagicMock()
            mock_inspector.get_schema_names.return_value = ["public"]
            mock_inspector.get_table_names.return_value = ["users"]
            mock_inspector.get_columns.return_value = [
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "VARCHAR"},
            ]
            mock_inspect.return_value = mock_inspector

            # Create connector with mocked components
            connector = PostgreSQLConnector(
                host="localhost", database="testdb", username="user", password="pass"
            )

            # Test get_schema method
            result = connector.get_schema()

            # Verify the result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2  # Two columns
            assert list(result.columns) == ["schema", "table", "column", "data_type"]
            assert list(result["column"]) == ["id", "name"]

    def test_get_schema_with_specific_schemas(self) -> None:
        """Test schema retrieval for specific schemas."""
        with (
            patch("sqldeps.database.postgresql.create_engine"),
            patch("sqldeps.database.postgresql.inspect") as mock_inspect,
        ):
            # Create mock inspector
            mock_inspector = MagicMock()
            mock_inspector.get_table_names.return_value = ["orders"]
            mock_inspector.get_columns.return_value = [
                {"name": "order_id", "type": "INTEGER"}
            ]
            mock_inspect.return_value = mock_inspector

            # Create connector with mocked components
            connector = PostgreSQLConnector(
                host="localhost", database="testdb", username="user", password="pass"
            )

            # Test get_schema method with specific schema
            result = connector.get_schema(schemas="sales")

            # Verify the result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert result["schema"][0] == "sales"
            assert result["table"][0] == "orders"
            assert result["column"][0] == "order_id"

    def test_pgpass_lookup(self) -> None:
        """Test .pgpass file password lookup."""
        pgpass_content = (
            "localhost:5432:testdb:user:secretpass\n*:5432:*:admin:adminpass"
        )

        with (
            patch("builtins.open", mock_open(read_data=pgpass_content)),
            patch.object(Path, "home", return_value=Path("/home/user")),
            patch.object(Path, "exists", return_value=True),
        ):
            # Test exact match
            password = PostgreSQLConnector._get_password_from_pgpass(
                None, "user", "localhost", "testdb", 5432, None
            )
            assert password == "secretpass"

            # Test wildcard match
            password = PostgreSQLConnector._get_password_from_pgpass(
                None, "admin", "somehost", "anydb", 5432, None
            )
            assert password == "adminpass"
