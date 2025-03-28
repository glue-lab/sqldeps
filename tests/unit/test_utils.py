"""Unit tests for utility functions in sqldeps.utils."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from sqldeps.models import SQLProfile
from sqldeps.utils import find_sql_files, merge_profiles, merge_schemas, schema_diff


class TestFileUtils:
    """Test file utility functions."""

    def test_find_sql_files(self):
        """Test finding SQL files in a directory."""
        # Mock a directory structure
        mock_files = [
            Path("folder/file1.sql"),
            Path("folder/file2.sql"),
            Path("folder/subdir/file3.sql"),
            Path("folder/file.txt"),
        ]

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("pathlib.Path.is_dir") as mock_is_dir,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            # Setup mocks
            mock_exists.return_value = True
            mock_is_dir.return_value = True
            mock_is_file.return_value = True

            # Non-recursive case: only top-level SQL files
            mock_glob.return_value = [
                Path("folder/file1.sql"),
                Path("folder/file2.sql"),
                Path("folder/file.txt"),
            ]

            result = find_sql_files("folder", recursive=False)
            assert len(result) == 2
            assert Path("folder/file1.sql") in result
            assert Path("folder/file2.sql") in result
            assert Path("folder/file.txt") not in result

            # Recursive case: all SQL files including subdirectories
            mock_glob.return_value = mock_files

            result = find_sql_files("folder", recursive=True)
            assert len(result) == 3
            assert Path("folder/file1.sql") in result
            assert Path("folder/file2.sql") in result
            assert Path("folder/subdir/file3.sql") in result
            assert Path("folder/file.txt") not in result

    def test_find_sql_files_custom_extensions(self):
        """Test finding files with custom extensions."""
        # Mock a directory structure
        mock_files = [
            Path("folder/file1.sql"),
            Path("folder/file2.hql"),
            Path("folder/file3.pgsql"),
            Path("folder/file.txt"),
        ]

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("pathlib.Path.is_dir") as mock_is_dir,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            # Setup mocks
            mock_exists.return_value = True
            mock_is_dir.return_value = True
            mock_is_file.return_value = True
            mock_glob.return_value = mock_files

            # Custom extensions
            result = find_sql_files(
                "folder", recursive=False, valid_extensions={"sql", "hql"}
            )
            assert len(result) == 2
            assert Path("folder/file1.sql") in result
            assert Path("folder/file2.hql") in result
            assert Path("folder/file3.pgsql") not in result

    def test_folder_not_found(self):
        """Test handling of folder not found."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(FileNotFoundError),
        ):
            find_sql_files("nonexistent")


class TestMergeProfiles:
    """Test merging of SQL profiles."""

    def test_merge_profiles(self) -> None:
        """
        Test merging multiple SQLProfile objects with different schemas, tables,
        and cases where '*' (wildcard) appears in column dependencies.

        Ensures:
        1. Unique tables are merged correctly.
        2. Columns are merged per table unless '*' is present.
        3. When '*' appears in a table's columns, it takes precedence,
        and other columns are ignored.
        4. Both dependencies and outputs are properly merged.
        """
        # First analysis: Normal tables with specific columns
        analysis1 = SQLProfile(
            dependencies={
                "public.users": ["id", "name"],  # Specific columns for 'users'
                "sales.orders": [
                    "order_id",
                    "user_id",
                ],  # Specific columns for 'orders'
            },
            outputs={
                "report.monthly_sales": ["month", "total_sales"],
            },
        )

        # Second analysis: A mix of specific columns and a wildcard '*'
        analysis2 = SQLProfile(
            dependencies={
                "sales.orders": [
                    "*"
                ],  # Wildcard '*' should override specific columns from analysis1
                "products": ["product_id", "name"],  # Specific columns for 'products'
            },
            outputs={
                "report.monthly_sales": [
                    "category"
                ],  # Adding a column to existing outcome
                "temp.product_summary": [
                    "product_id",
                    "sales_count",
                ],  # New outcome table
            },
        )

        # Third analysis: Another table and more columns for 'users'
        analysis3 = SQLProfile(
            dependencies={
                "public.users": ["email"],  # Adding 'email' to 'users' table
                "payments": [
                    "payment_id",
                    "user_id",
                ],  # Specific columns for 'payments'
            },
            outputs={
                "report.user_activity": ["user_id", "last_login"],  # New outcome table
                "temp.product_summary": [
                    "*"
                ],  # Wildcard should override specific columns
            },
        )

        # Merge all analyses together
        merged_analysis = merge_profiles([analysis1, analysis2, analysis3])

        # Expected merged result: Distinct tables and merged columns
        # for both dependencies and outputs
        expected_result = SQLProfile(
            dependencies={
                "payments": [
                    "payment_id",
                    "user_id",
                ],  # Payments should contain both columns
                "products": ["name", "product_id"],  # Products should remain unchanged
                "public.users": [
                    "email",
                    "id",
                    "name",
                ],  # Users should include all unique columns
                "sales.orders": [
                    "*"
                ],  # '*' takes precedence and should be the only column here
            },
            outputs={
                "report.monthly_sales": [
                    "category",
                    "month",
                    "total_sales",
                ],  # Combined columns from analysis1 and analysis2
                "report.user_activity": ["last_login", "user_id"],  # From analysis3
                "temp.product_summary": ["*"],  # '*' takes precedence from analysis3
            },
        )

        # Validate that the merged analysis matches the expected result
        assert merged_analysis.to_dict() == expected_result.to_dict(), (
            "Merged SQL analyses do not match expected output"
        )


class TestSchemaMerging:
    """Test schema merging and validation."""

    def test_merge_schemas(self) -> None:
        """
        Tests all combinations of schema/table/column matches including:
        - Wildcards (*)
        - No columns (None)
        - Exact schema matches
        - Schema-agnostic matches

        Test Matrix:
        Schema  Table   Column  Expected
        ------  ------  ------  --------
        yes     yes     yes     Exact match
        yes     yes     *       Exact match for all columns
        yes     yes     None    Exact match with no columns
        yes     no      yes     No match (non-existent table)
        yes     no      None    No match (non-existent table)
        no      yes     yes     Schema-agnostic match
        no      yes     *       Schema-agnostic match for all columns
        no      yes     None    Schema-agnostic match with no columns
        no      no      yes     No match (non-existent table)
        no      no      None    No match (non-existent table)
        """
        # Database schema
        db_records = [
            # schema1.table1 (primary test table)
            ["schema1", "table1", "col1", "type1"],
            ["schema1", "table1", "col2", "type1"],
            # schema2.table1 (same table, different schema)
            ["schema2", "table1", "col1", "type1"],
            ["schema2", "table1", "col3", "type1"],
            # schema1.table2 (different table)
            ["schema1", "table2", "col4", "type1"],
            # schema2.table3 (unique table)
            ["schema2", "table3", "col5", "type1"],
        ]
        df_db = pd.DataFrame(
            db_records, columns=["schema", "table", "column", "data_type"]
        )

        # Test all combinations
        test_records = [
            # Schema-specific matches
            ["schema1", "table1", "col1"],  # Direct match
            ["schema1", "table1", "*"],  # Wildcard in specific schema
            ["schema1", "table1", None],  # No columns with schema
            ["schema1", "missing", "col1"],  # Non-existent table
            ["schema1", "missing", None],  # Non-existent table, no columns
            ["schema3", "table1", "col1"],  # Non-existent schema
            # Schema-agnostic matches
            [None, "table1", "col1"],  # Match across schemas
            [None, "table1", "*"],  # Wildcard across schemas
            [None, "table1", None],  # No columns, schema-agnostic
            [None, "missing", "col1"],  # Non-existent table
            [None, "missing", None],  # Non-existent table, no columns
            [None, "table1", "missing"],  # Non-existent column
        ]
        df_test = pd.DataFrame(test_records, columns=["schema", "table", "column"])

        # Expected results
        expected_records = [
            # schema1.table1 matches
            ["schema1", "table1", "col1", "type1", True],  # Direct match
            ["schema1", "table1", "col2", "type1", True],  # From schema1 wildcard
            ["schema1", "table1", None, None, True],  # No columns, exact schema
            # schema2.table1 matches (schema-agnostic)
            ["schema2", "table1", "col1", "type1", False],  # Schema-agnostic match
            ["schema2", "table1", "col3", "type1", False],  # From agnostic wildcard
            ["schema2", "table1", None, None, False],  # No columns, schema-agnostic
        ]
        df_expected = (
            pd.DataFrame(
                data=expected_records,
                columns=["schema", "table", "column", "data_type", "exact_match"],
            )
            .sort_values(
                by=["schema", "table", "column", "data_type", "exact_match"],
                ascending=[True, True, True, True, False],
                na_position="last",
            )
            .assign(exact_match=lambda x: x.exact_match.astype("boolean"))
            .reset_index(drop=True)
        )

        # Run merge_schemas
        result = merge_schemas(df_test, df_db)

        # Verify results match expectations
        pd.testing.assert_frame_equal(result, df_expected)

        # Additional assertions

        # Test 1: Verify schema1.table1 matches (including None columns)
        schema1_matches = result[result["schema"] == "schema1"]
        assert len(schema1_matches) == 3  # Two columns + one None
        assert all(schema1_matches["exact_match"])

        # Test 2: Verify schema2.table1 matches (including None columns)
        schema2_matches = result[result["schema"] == "schema2"]
        assert len(schema2_matches) == 3  # Two columns + one None
        assert not any(schema2_matches["exact_match"])

        # Test 3: Verify non-matches
        assert "missing" not in result["table"].values
        assert "missing" not in result["column"].values
        assert "schema3" not in result["schema"].values

        # Test 4: Verify no duplicates
        assert not result.duplicated().any()

        # Test 5: Verify None columns are properly handled
        none_cols = result[result["column"].isna()]
        assert len(none_cols) == 2  # One exact match, one schema-agnostic
        assert sum(none_cols["exact_match"]) == 1  # One exact match

    def test_edge_cases(self) -> None:
        """Test edge cases for merge_schemas"""
        # Minimal database schema
        db_records = [
            ["schema1", "table1", "col1", "type1"],
            ["schema1", "table1", "col2", "type1"],
            ["schema2", "table1", "col1", "type1"],
        ]
        df_db = pd.DataFrame(
            db_records, columns=["schema", "table", "column", "data_type"]
        )

        # Test case 1: Empty input
        df_empty = pd.DataFrame(columns=["schema", "table", "column"])
        result_empty = merge_schemas(df_empty, df_db)
        assert len(result_empty) == 0

        # Test case 2: Mix of wildcards and None columns
        df_mixed = pd.DataFrame(
            [
                ["schema1", "table1", "*"],  # Wildcard with schema
                ["schema1", "table1", None],  # None with schema
                [None, "table1", "*"],  # Schema-agnostic wildcard
                [None, "table1", None],  # Schema-agnostic None
            ],
            columns=["schema", "table", "column"],
        )
        result_mixed = merge_schemas(df_mixed, df_db)

        # Verify mixed results
        assert (
            len(result_mixed) == 5
        )  # 2 columns + 1 None (exact) + 2 columns (agnostic)
        assert (
            sum(result_mixed["exact_match"]) == 3
        )  # Two columns + one None from exact matches
        assert (
            sum(result_mixed["column"].isna()) == 2
        )  # Two None entries (one exact, one agnostic)

        # Test case 3: Only None columns
        df_none = pd.DataFrame(
            [
                ["schema1", "table1", None],
                [None, "table1", None],
            ],
            columns=["schema", "table", "column"],
        )
        result_none = merge_schemas(df_none, df_db)
        assert len(result_none) == 2  # One exact match, one schema-agnostic
        assert sum(result_none["exact_match"]) == 1  # One exact match
        assert all(result_none["column"].isna())  # All columns should be None

    def test_schema_diff(self) -> None:
        """
        Test the optimized schema_diff function with comprehensive scenarios.
        """
        # Setup test data
        db_records = [
            ["schema1", "users", "id", "INTEGER"],
            ["schema1", "users", "email", "VARCHAR"],
            ["schema2", "users", "id", "INTEGER"],
            ["schema2", "orders", "id", "INTEGER"],
        ]
        df_db = pd.DataFrame(
            db_records, columns=["schema", "table", "column", "data_type"]
        )

        test_records = [
            # Exact matches (should exist)
            ["schema1", "users", "id"],
            ["schema2", "orders", "id"],
            # Non-existent combinations
            ["schema1", "users", "nonexistent"],
            ["schema3", "users", "id"],
            # Wildcards with schema
            ["schema1", "users", "*"],
            ["schema3", "users", "*"],
            # Schema-agnostic matches
            [None, "users", "id"],
            [None, "users", "nonexistent"],
            # Schema-agnostic wildcards
            [None, "users", "*"],
            [None, "nonexistent", "*"],
        ]
        df_test = pd.DataFrame(test_records, columns=["schema", "table", "column"])

        # Run schema_diff
        result = schema_diff(df_test, df_db)

        # Verify results
        expected_exists = [
            True,  # schema1.users.id exists
            True,  # schema2.orders.id exists
            False,  # schema1.users.nonexistent doesn't exist
            False,  # schema3.users.id doesn't exist
            True,  # schema1.users.* matches
            False,  # schema3.users.* doesn't match
            True,  # agnostic users.id exists
            False,  # agnostic users.nonexistent doesn't exist
            True,  # agnostic users.* matches
            False,  # agnostic nonexistent.* doesn't match
        ]

        assert all(result["match_db"] == expected_exists)

        # Test edge cases
        empty_df = pd.DataFrame(columns=["schema", "table", "column"])
        empty_result = schema_diff(empty_df, df_db)
        assert len(empty_result) == 0

        single_row = pd.DataFrame(
            [["schema1", "users", "*"]], columns=["schema", "table", "column"]
        )
        single_result = schema_diff(single_row, df_db)
        assert single_result["match_db"].iloc[0] is np.True_
