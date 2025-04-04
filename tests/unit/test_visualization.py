"""Unit tests for visualization.py."""

from sqldeps.models import SQLProfile
from sqldeps.visualization import visualize_sql_dependencies


def test_visualize_sql_dependencies_basic():
    """Test basic visualization of SQL dependencies."""
    # Simple mock dependencies data
    sql_profiles = {
        "file1.sql": SQLProfile(
            dependencies={"table1": ["col1", "col2"]}, outputs={"table2": ["col3"]}
        ),
    }

    # Call the visualization function
    figure = visualize_sql_dependencies(sql_profiles)

    # Basic assertions to verify the figure was created properly
    assert figure is not None
    assert len(figure.data) > 0  # Should have at least some traces

    # Verify title contains expected information
    assert "SQL Dependency Graph" in figure.layout.title.text
    assert "1 files" in figure.layout.title.text


def test_visualize_sql_dependencies_empty():
    """Test visualization with empty dependencies."""
    # Call with empty dependencies
    figure = visualize_sql_dependencies({})

    # Should still create a figure
    assert figure is not None
    assert "0 files" in figure.layout.title.text
