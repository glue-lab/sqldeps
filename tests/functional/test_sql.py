# tests/functional/test_sql.py
import json
from pathlib import Path

import pytest

TEST_DATA_DIR = Path(__file__).parent.parent / "data"
SQL_DIR = TEST_DATA_DIR / "sql"
EXPECTED_OUTPUT_DIR = TEST_DATA_DIR / "expected_outputs"


# Create a list of test cases from data directory
def get_test_cases():
    test_cases = []
    for sql_file in SQL_DIR.glob("example*.sql"):
        expected_file = EXPECTED_OUTPUT_DIR / f"{sql_file.stem}_expected.json"
        if expected_file.exists():
            test_cases.append((sql_file, expected_file))
    return test_cases


@pytest.mark.parametrize("sql_file,expected_output_file", get_test_cases())
@pytest.mark.llm
def test_sql_dependency_extraction(sql_file, expected_output_file, extractor):
    """Test extraction of dependencies from SQL files."""
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
