"""Integration tests for database connectors.

These tests connect to an actual PostgreSQL database to verify
schema retrieval and validation functionality.
"""

import os

import pandas as pd
import pytest

from sqldeps.database import PostgreSQLConnector

# Skip all tests if no test database is configured
pytestmark = [
    pytest.mark.skipif(
        os.environ.get("TEST_DB_HOST") is None, reason="Test database not configured"
    ),
    pytest.mark.integration,
]


class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL connector.

    To run these tests, set the following environment variables:
    - TEST_DB_HOST
    - TEST_DB_PORT (optional, defaults to 5432)
    - TEST_DB_NAME
    - TEST_DB_USER
    - TEST_DB_PASSWORD
    """

    @pytest.fixture
    def db_connector(self) -> PostgreSQLConnector:
        """Create a database connector for testing.

        Returns:
            PostgreSQLConnector: Configured database connector
        """
        return PostgreSQLConnector(
            host=os.environ.get("TEST_DB_HOST"),
            port=int(os.environ.get("TEST_DB_PORT", "5432")),
            database=os.environ.get("TEST_DB_NAME"),
            username=os.environ.get("TEST_DB_USER"),
            password=os.environ.get("TEST_DB_PASSWORD"),
        )

    def test_connection(self, db_connector: PostgreSQLConnector) -> None:
        """Test that connection to database succeeds."""
        # Just creating the connector should establish a connection
        # If it doesn't, an exception will be raised and the test will fail
        assert db_connector is not None
        assert hasattr(db_connector, "engine")
        assert hasattr(db_connector, "inspector")

    def test_get_schema(self, db_connector: PostgreSQLConnector) -> None:
        """Test retrieving schema information."""
        # Get schema for the public schema
        schema = db_connector.get_schema("public")

        # Verify result structure
        assert isinstance(schema, pd.DataFrame)
        assert set(schema.columns) == {"schema", "table", "column", "data_type"}
        assert len(schema) > 0  # Should have at least some tables

        # Verify all rows have the correct schema
        assert all(schema["schema"] == "public")

    # Commented out because it takes too long to run
    # @pytest.mark.slow
    # def test_get_schema_multiple(self, db_connector):
    #     """Test retrieving schema from multiple schemas."""
    #     # Get schema from all available schemas
    #     schema = db_connector.get_schema()

    #     # Verify result
    #     assert isinstance(schema, pd.DataFrame)
    #     assert len(schema) > 0

    #     # Should include multiple schemas if available
    #     schemas = schema["schema"].unique()
    #     assert len(schemas) > 0

    def test_export_schema_csv(
        self, db_connector: PostgreSQLConnector, tmp_path: str
    ) -> None:
        """Test exporting schema to CSV.

        Args:
            db_connector: PostgreSQL connector fixture
            tmp_path: Pytest temporary path fixture
        """
        # Export schema to a temporary file
        output_file = tmp_path / "schema.csv"
        db_connector.export_schema_csv(output_file, schemas="public")

        # Verify file was created
        assert output_file.exists()

        # Verify file content
        df = pd.read_csv(output_file)
        assert set(df.columns) == {"schema", "table", "column", "data_type"}
        assert len(df) > 0
