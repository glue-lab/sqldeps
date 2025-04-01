"""Functional tests for SQL dependency extraction.

This module tests the end-to-end functionality of SQL dependency extraction
against a set of predefined SQL files with expected outputs.
"""

import json
from pathlib import Path

import pytest

from sqldeps.llm_parsers import BaseSQLExtractor

TEST_DATA_DIR = Path(__file__).parent.parent / "data"
SQL_DIR = TEST_DATA_DIR / "sql"
EXPECTED_OUTPUT_DIR = TEST_DATA_DIR / "expected_outputs"


# Create a list of test cases from data directory
def get_test_cases() -> list:
    """Create a list of test cases from data directory.

    Each test case is a tuple of (sql_file, expected_output_file).

    Returns:
        list: List of test case tuples
    """
    test_cases = []
    for sql_file in SQL_DIR.glob("example*.sql"):
        expected_file = EXPECTED_OUTPUT_DIR / f"{sql_file.stem}_expected.json"
        if expected_file.exists():
            test_cases.append((sql_file, expected_file))
    return test_cases


@pytest.mark.parametrize("sql_file,expected_output_file", get_test_cases())
@pytest.mark.llm
def test_sql_dependency_extraction(
    sql_file: Path, expected_output_file: Path, extractor: BaseSQLExtractor
) -> None:
    """Test extraction of dependencies from SQL files.

    Args:
        sql_file: Path to SQL file
        expected_output_file: Path to expected output JSON file
        extractor: SQLDeps extractor fixture
    """
    # Load SQL code
    with open(sql_file) as f:
        sql = f.read()

    # Load expected output
    with open(expected_output_file) as f:
        expected_output = json.load(f)

    # Run the extractor
    dependency = extractor.extract_from_query(sql)

    # Assert the output matches the expected
    assert dependency.to_dict() == expected_output
