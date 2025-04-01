"""Unit tests for the SQLDeps web application.

This module tests the web application's UI elements, data processing,
and error handling without requiring an actual browser.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from sqldeps.models import SQLProfile


@pytest.fixture
def mock_sql_profile() -> SQLProfile:
    """Create a mock SQLProfile for testing.

    Returns:
        SQLProfile: A sample SQLProfile for testing
    """
    return SQLProfile(
        dependencies={
            "users": ["id", "name", "email"],
            "orders": ["id", "order_date", "user_id"],
        },
        outputs={
            "user_summary": ["user_id", "total_orders"],
        },
    )


class TestAppMain:
    """Test suite for app/main.py."""

    @patch("streamlit.set_page_config")
    def test_app_configuration(self, mock_set_page_config: MagicMock) -> None:
        """Test the app sets the correct page configuration."""
        # Import the app module to trigger set_page_config
        # Reload to ensure set_page_config is called
        import importlib

        import sqldeps.app.main

        importlib.reload(sqldeps.app.main)

        # Verify set_page_config was called with expected arguments
        mock_set_page_config.assert_called()
        call_args = mock_set_page_config.call_args[1]
        assert call_args["page_title"] == "SQL Dependency Extractor"
        assert call_args["layout"] == "wide"

    @patch("sqldeps.app.main.st")
    @patch("sqldeps.app.main.Path")
    def test_basic_ui_elements(self, mock_path: MagicMock, mock_st: MagicMock) -> None:
        """Test basic UI elements are created."""
        # Setup mocks
        mock_logo_path = MagicMock()
        mock_path.return_value.parent.return_value.joinpath.return_value = (
            mock_logo_path
        )
        mock_st.sidebar.selectbox.side_effect = ["groq", "model"]
        mock_st.sidebar.file_uploader.return_value = None
        mock_st.sidebar.checkbox.return_value = False
        mock_st.sidebar.radio.return_value = "Enter SQL Query"
        mock_st.sidebar.text_area.return_value = ""
        mock_st.sidebar.button.return_value = False
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Import and run the main function
        from sqldeps.app.main import main

        main()

        # Verify basic UI elements were created
        mock_st.title.assert_called()
        mock_st.sidebar.image.assert_called()
        mock_st.sidebar.header.assert_called()
        mock_st.columns.assert_called()

    @patch("sqldeps.app.main.create_extractor")
    @patch("sqldeps.app.main.st")
    @patch("sqldeps.app.main.Path")
    @patch("sqldeps.app.main.sqlparse")
    def test_sql_processing(
        self,
        mock_sqlparse: MagicMock,
        mock_path: MagicMock,
        mock_st: MagicMock,
        mock_create_extractor: MagicMock,
        mock_sql_profile: SQLProfile,
    ) -> None:
        """Test SQL processing with a text input.

        Args:
            mock_sqlparse: Mock for sqlparse module
            mock_path: Mock for Path class
            mock_st: Mock for streamlit module
            mock_create_extractor: Mock for create_extractor function
            mock_sql_profile: SQLProfile fixture
        """
        # Setup mocks
        mock_logo_path = MagicMock()
        mock_path.return_value.parent.return_value.joinpath.return_value = (
            mock_logo_path
        )
        mock_st.sidebar.selectbox.side_effect = ["groq", "model"]
        mock_st.sidebar.file_uploader.return_value = None
        mock_st.sidebar.checkbox.return_value = False
        mock_st.sidebar.radio.return_value = "Enter SQL Query"
        mock_st.sidebar.text_area.return_value = "SELECT * FROM users"
        mock_st.sidebar.button.return_value = True
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Setup sqlparse mock
        mock_sqlparse.format.return_value = "SELECT * FROM users"

        # Setup extractor mock
        mock_extractor = MagicMock()
        mock_extractor.extract_from_query.return_value = mock_sql_profile
        mock_create_extractor.return_value = mock_extractor

        # Import and run the main function
        from sqldeps.app.main import main

        main()

        # Verify SQL was processed
        mock_create_extractor.assert_called()
        mock_extractor.extract_from_query.assert_called_with("SELECT * FROM users")

    @patch("sqldeps.app.main.create_extractor")
    @patch("sqldeps.app.main.st")
    @patch("sqldeps.app.main.Path")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_sql_file_upload(
        self,
        mock_unlink: MagicMock,
        mock_tempfile: MagicMock,
        mock_path: MagicMock,
        mock_st: MagicMock,
        mock_create_extractor: MagicMock,
        mock_sql_profile: SQLProfile,
    ) -> None:
        """Test SQL file upload processing.

        Args:
            mock_unlink: Mock for os.unlink
            mock_tempfile: Mock for tempfile.NamedTemporaryFile
            mock_path: Mock for Path class
            mock_st: Mock for streamlit module
            mock_create_extractor: Mock for create_extractor function
            mock_sql_profile: SQLProfile fixture
        """
        # Setup mocks
        mock_logo_path = MagicMock()
        mock_path.return_value.parent.return_value.joinpath.return_value = (
            mock_logo_path
        )

        # Create a mock file
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"SELECT * FROM users"

        # Setup streamlit mocks
        mock_st.sidebar.selectbox.side_effect = ["groq", "model"]
        mock_st.sidebar.file_uploader.return_value = mock_file
        mock_st.sidebar.checkbox.return_value = False
        mock_st.sidebar.radio.return_value = "Upload SQL File"
        mock_st.sidebar.button.return_value = True
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Setup temp file mock
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.sql"
        mock_tempfile.return_value.__enter__.return_value = mock_temp

        # Setup extractor mock
        mock_extractor = MagicMock()
        mock_extractor.extract_from_file.return_value = mock_sql_profile
        mock_create_extractor.return_value = mock_extractor

        # Import and run the main function
        from sqldeps.app.main import main

        main()

        # Verify file was processed
        # Note we're not checking call count since that depends on implementation
        mock_temp.write.assert_called_with(b"SELECT * FROM users")
        mock_extractor.extract_from_file.assert_called()
        mock_unlink.assert_called()

    @patch("sqldeps.app.main.create_extractor")
    @patch("sqldeps.app.main.PostgreSQLConnector")
    @patch("sqldeps.app.main.st")
    @patch("sqldeps.app.main.Path")
    @patch("sqldeps.app.main.sqlparse")
    def test_database_validation(
        self,
        mock_sqlparse: MagicMock,
        mock_path: MagicMock,
        mock_st: MagicMock,
        mock_db_connector: MagicMock,
        mock_create_extractor: MagicMock,
        mock_sql_profile: SQLProfile,
    ) -> None:
        """Test database validation functionality.

        Args:
            mock_sqlparse: Mock for sqlparse module
            mock_path: Mock for Path class
            mock_st: Mock for streamlit module
            mock_db_connector: Mock for PostgreSQLConnector
            mock_create_extractor: Mock for create_extractor function
            mock_sql_profile: SQLProfile fixture
        """
        # Setup mocks
        mock_logo_path = MagicMock()
        mock_path.return_value.parent.return_value.joinpath.return_value = (
            mock_logo_path
        )

        # Setup streamlit mocks
        mock_st.sidebar.selectbox.side_effect = ["groq", "model"]
        mock_st.sidebar.file_uploader.return_value = None
        mock_st.sidebar.checkbox.return_value = True  # Enable DB validation
        mock_st.sidebar.text_input.side_effect = ["localhost", "mydb", "user", "public"]
        mock_st.sidebar.number_input.return_value = 5432
        mock_st.sidebar.radio.return_value = "Enter SQL Query"
        mock_st.sidebar.text_area.return_value = "SELECT * FROM users"
        mock_st.sidebar.button.return_value = True
        mock_st.columns.return_value = [MagicMock(), MagicMock()]

        # Setup sqlparse mock
        mock_sqlparse.format.return_value = "SELECT * FROM users"

        # Setup DB mock
        mock_db = MagicMock()
        mock_db_connector.return_value = mock_db

        # Setup DB validation result
        db_result = pd.DataFrame(
            {
                "schema": ["public"],
                "table": ["users"],
                "column": ["id"],
                "data_type": ["integer"],
                "exact_match": [True],
            }
        )

        # Setup extractor mock
        mock_extractor = MagicMock()
        mock_extractor.extract_from_query.return_value = mock_sql_profile
        mock_extractor.match_database_schema.return_value = db_result
        mock_create_extractor.return_value = mock_extractor

        # Import and run the main function
        from sqldeps.app.main import main

        main()

        # Verify database validation was performed
        mock_db_connector.assert_called_with(
            host="localhost", port=5432, database="mydb", username="user"
        )
        mock_extractor.match_database_schema.assert_called()

    @patch("sqldeps.app.main.create_extractor")
    @patch("sqldeps.app.main.st")
    @patch("sqldeps.app.main.Path")
    @patch("sqldeps.app.main.sqlparse")
    def test_error_handling_alternative(
        self,
        mock_sqlparse: MagicMock,
        mock_path: MagicMock,
        mock_st: MagicMock,
        mock_create_extractor: MagicMock,
    ) -> None:
        """Test error handling in the app by checking overall control flow.

        Args:
            mock_sqlparse: Mock for sqlparse module
            mock_path: Mock for Path class
            mock_st: Mock for streamlit module
            mock_create_extractor: Mock for create_extractor function
        """
        # Setup mocks
        mock_logo_path = MagicMock()
        mock_path.return_value.parent.return_value.joinpath.return_value = (
            mock_logo_path
        )

        # Setup streamlit mocks
        mock_st.sidebar.selectbox.side_effect = ["groq", "model"]
        mock_st.sidebar.file_uploader.return_value = None
        mock_st.sidebar.checkbox.return_value = False
        mock_st.sidebar.radio.return_value = "Enter SQL Query"
        mock_st.sidebar.text_area.return_value = "SELECT * FROM users"
        mock_st.sidebar.button.return_value = True

        # Setup columns
        col1 = MagicMock()
        col2 = MagicMock()
        mock_st.columns.return_value = [col1, col2]

        # Setup sqlparse mock
        mock_sqlparse.format.return_value = "SELECT * FROM users"

        # Make create_extractor raise an exception
        mock_create_extractor.side_effect = ValueError("API key not found")

        # Import and run the main function
        from sqldeps.app.main import main

        # Run the function - this should trigger exception handling
        main()

        # Verify that the main flow completed without raising an exception
        # If we got here without an exception, the error handling is working
        assert True
