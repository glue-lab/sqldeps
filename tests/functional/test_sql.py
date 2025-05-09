"""Functional tests for SQL dependency extraction.

This module tests the end-to-end functionality of SQL dependency extraction
against a set of predefined SQL files with expected outputs.

The module provides two testing approaches:
1. A fast batch test (test_sql_dependency_extraction_batch) that extracts
   dependencies from all SQL files at once using parallel processing
2. A slower individual test (test_sql_dependency_extraction_individual) that
   processes each file separately, which is useful for debugging specific files

The batch approach is more efficient as it leverages parallel processing
and extracts dependencies from all files in a single operation.
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


def load_expected_output(expected_output_file: Path) -> dict:
    """Load the expected output from a JSON file.

    Args:
        expected_output_file: Path to the expected output JSON file

    Returns:
        dict: The expected output as a dictionary
    """
    with open(expected_output_file) as f:
        return json.load(f)


@pytest.mark.llm
def test_sql_dependency_extraction_batch(extractor: BaseSQLExtractor) -> None:
    """Test extraction of dependencies from all SQL files at once.

    This is more efficient than testing each file individually as it
    extracts dependencies from all files in a single batch.

    Args:
        extractor: SQLDeps extractor fixture
    """
    # Get all the test cases
    test_cases = get_test_cases()

    # Extract dependencies from all SQL files at once
    results = extractor.extract_from_folder(
        SQL_DIR, recursive=False, n_workers=-1, use_cache=False, rpm=100
    )

    # Verify each result against its expected output
    for sql_file, expected_output_file in test_cases:
        expected_output = load_expected_output(expected_output_file)
        extracted = results[str(sql_file)].to_dict()

        # Use a more descriptive assertion message
        assert extracted == expected_output, f"Mismatch for {sql_file.name}"


# Keep the original test for backward compatibility but mark it as slow
@pytest.mark.parametrize(
    "sql_file,expected_output_file",
    get_test_cases(),
    ids=lambda x: x.name if isinstance(x, Path) else str(x),
)
@pytest.mark.llm
@pytest.mark.slow
def test_sql_dependency_extraction_individual(
    sql_file: Path, expected_output_file: Path, extractor: BaseSQLExtractor
) -> None:
    """Test extraction of dependencies from SQL files individually.

    This is slower than the batch test but useful for debugging specific files.
    This test will only run when both 'llm' and 'slow' markers are specified.

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
    assert dependency.to_dict() == expected_output, f"Mismatch for {sql_file.name}"
