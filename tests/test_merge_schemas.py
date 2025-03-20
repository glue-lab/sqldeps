import pandas as pd

from sqldeps.utils import merge_schemas


def test_merge_schemas() -> None:
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
    df_db = pd.DataFrame(db_records, columns=["schema", "table", "column", "data_type"])

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


def test_edge_cases() -> None:
    """Test edge cases for merge_schemas"""
    # Minimal database schema
    db_records = [
        ["schema1", "table1", "col1", "type1"],
        ["schema1", "table1", "col2", "type1"],
        ["schema2", "table1", "col1", "type1"],
    ]
    df_db = pd.DataFrame(db_records, columns=["schema", "table", "column", "data_type"])

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
    assert len(result_mixed) == 5  # 2 columns + 1 None (exact) + 2 columns (agnostic)
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
