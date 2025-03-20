import pandas as pd

from sqldeps.utils import schema_diff


def test_schema_diff() -> None:
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
    df_db = pd.DataFrame(db_records, columns=["schema", "table", "column", "data_type"])

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
    assert bool(single_result["match_db"].iloc[0]) is True
