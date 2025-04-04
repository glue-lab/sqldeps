"""Unit tests for data models.

This module tests the SQLProfile class and its methods.
"""

import pandas as pd

from sqldeps.models import SQLProfile


def test_sql_profile_initialization() -> None:
    """Test SQLProfile initialization and sorting."""
    # Create a profile with unsorted data
    profile = SQLProfile(
        dependencies={
            "table_b": ["col_c", "col_a", "col_b"],
            "table_a": ["col_z", "col_y"],
        },
        outputs={
            "schema.out_table_b": ["out_col_b", "out_col_a"],
            "schema.out_table_a": ["out_col_x"],
        },
    )

    # Check that tables and columns are sorted
    assert list(profile.dependencies.keys()) == ["table_a", "table_b"]
    assert profile.dependencies["table_a"] == ["col_y", "col_z"]
    assert profile.dependencies["table_b"] == ["col_a", "col_b", "col_c"]

    assert list(profile.outputs.keys()) == ["schema.out_table_a", "schema.out_table_b"]
    assert profile.outputs["schema.out_table_a"] == ["out_col_x"]
    assert profile.outputs["schema.out_table_b"] == ["out_col_a", "out_col_b"]


def test_to_dataframe_conversion() -> None:
    """Test conversion to DataFrame with proper structure."""
    profile = SQLProfile(
        dependencies={"schema.users": ["id", "name"]},
        outputs={"public.user_report": ["user_id", "report_date"]},
    )

    df = profile.to_dataframe()

    # Check DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"type", "schema", "table", "column"}

    # Check dependencies were properly converted
    deps = df[df["type"] == "dependency"]
    assert len(deps) == 2  # Two columns
    assert set(deps["schema"]) == {"schema"}
    assert set(deps["table"]) == {"users"}
    assert set(deps["column"]) == {"id", "name"}

    # Check outputs were properly converted
    outs = df[df["type"] == "outcome"]
    assert len(outs) == 2  # Two columns
    assert set(outs["schema"]) == {"public"}
    assert set(outs["table"]) == {"user_report"}
    assert set(outs["column"]) == {"user_id", "report_date"}


def test_empty_columns_handling() -> None:
    """Test handling of tables with no specific columns."""
    profile = SQLProfile(
        dependencies={"table_with_no_columns": []},
        outputs={"output_table_no_columns": []},
    )

    df = profile.to_dataframe()

    # Check tables with no columns are properly represented
    deps = df[df["type"] == "dependency"]
    assert len(deps) == 1
    assert deps.iloc[0]["table"] == "table_with_no_columns"
    assert deps.iloc[0]["column"] is None

    outs = df[df["type"] == "outcome"]
    assert len(outs) == 1
    assert outs.iloc[0]["table"] == "output_table_no_columns"
    assert outs.iloc[0]["column"] is None


def test_to_dict() -> None:
    """Test conversion to dictionary format."""
    profile = SQLProfile(
        dependencies={"users": ["id", "name"]}, outputs={"reports": ["user_id"]}
    )

    result = profile.to_dict()

    assert isinstance(result, dict)
    assert "dependencies" in result
    assert "outputs" in result
    assert result["dependencies"] == {"users": ["id", "name"]}
    assert result["outputs"] == {"reports": ["user_id"]}


def test_property_accessors() -> None:
    """Test property accessor methods."""
    profile = SQLProfile(
        dependencies={"schema1.table1": ["col1"], "schema2.table2": ["col2"]},
        outputs={"schema3.table3": ["col3"], "schema4.table4": ["col4"]},
    )

    # Test dependency_tables property
    assert profile.dependency_tables == ["schema1.table1", "schema2.table2"]

    # Test outcome_tables property
    assert profile.outcome_tables == ["schema3.table3", "schema4.table4"]
