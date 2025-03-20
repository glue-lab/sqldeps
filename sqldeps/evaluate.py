import json
import os
import time

from sqldeps.llm_parsers import create_extractor


def run_extractor_with_retry(extractor, sql, max_trials=3, sleep_time=10):
    """Runs the extractor and measures execution time, with retry logic.

    Args:
        extractor: The extractor object with an extract_from_query method.
        sql: The SQL query string.
        max_trials: The maximum number of retry attempts.
        sleep_time: sleep time between trials in seconds.

    Returns:
        A tuple containing:
            - The result of the extraction (if successful), or None if all trials fail.
            - The execution time (if successful), or None if all trials fail.
    """
    trials = 0
    while trials < max_trials:
        try:
            start_time = time.time()
            result = extractor.extract_from_query(sql)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            trials += 1
            print(f"Trial {trials} failed: {e}")
            if trials == max_trials:
                print(f"All {max_trials} trials failed. Extraction unsuccessful.")
                return None, None
            else:
                time.sleep(sleep_time)


def compare_extraction_results(extracted, expected):
    """Compares extracted SQL dependencies with expected results and
    calculates performance metrics.

    Args:
        extracted: Dictionary containing the extracted dependencies
        expected: Dictionary containing the expected dependencies (ground truth)

    Returns:
        Dictionary containing detailed comparison metrics
    """
    # Calculate metrics for tables
    expected_tables = set(expected["tables"])
    extracted_tables = set(extracted["tables"])

    true_positive_tables = expected_tables.intersection(extracted_tables)
    false_positive_tables = extracted_tables - expected_tables
    false_negative_tables = expected_tables - extracted_tables

    # Create sets of (table, column) pairs for proper comparison
    expected_table_columns = set()
    for table, columns in expected["columns"].items():
        for column in columns:
            expected_table_columns.add((table, column))

    extracted_table_columns = set()
    for table, columns in extracted["columns"].items():
        for column in columns:
            extracted_table_columns.add((table, column))

    # Calculate column metrics using the pairs
    true_positive_columns = len(
        expected_table_columns.intersection(extracted_table_columns)
    )
    false_positive_columns = len(extracted_table_columns - expected_table_columns)
    false_negative_columns = len(expected_table_columns - extracted_table_columns)

    # Calculate precision and recall
    table_precision = (
        len(true_positive_tables) / len(extracted_tables) if extracted_tables else 0
    )
    table_recall = (
        len(true_positive_tables) / len(expected_tables) if expected_tables else 0
    )
    table_f1 = (
        2 * table_precision * table_recall / (table_precision + table_recall)
        if (table_precision + table_recall)
        else 0
    )

    column_precision = (
        true_positive_columns / (true_positive_columns + false_positive_columns)
        if (true_positive_columns + false_positive_columns)
        else 0
    )
    column_recall = (
        true_positive_columns / (true_positive_columns + false_negative_columns)
        if (true_positive_columns + false_negative_columns)
        else 0
    )
    column_f1 = (
        2 * column_precision * column_recall / (column_precision + column_recall)
        if (column_precision + column_recall)
        else 0
    )

    # Calculate overall exact match and table coverage
    exact_match = extracted == expected
    all_tables_in_columns = all(
        table in extracted["columns"] for table in extracted["tables"]
    )

    return {
        "exact_match": exact_match,
        "all_tables_in_columns": all_tables_in_columns,
        "tbl_TP": len(true_positive_tables),
        "tbl_FP": len(false_positive_tables),
        "tbl_FN": len(false_negative_tables),
        "tbl_precision": table_precision,
        "tbl_recall": table_recall,
        "tbl_f1": table_f1,
        "col_TP": true_positive_columns,
        "col_FP": false_positive_columns,
        "col_FN": false_negative_columns,
        "col_precision": column_precision,
        "col_recall": column_recall,
        "col_f1": column_f1,
    }


def evaluate_extraction_performance(
    framework, model, sql_file, expected_json_file, prompt_path=None
):
    """Evaluates SQL dependency extraction performance with detailed metrics.

    Args:
        framework: The LLM framework to use (e.g., "groq", "openai")
        model: The model name to use
        sql_file: Path to the SQL file to analyze
        expected_json_file: Path to the expected results JSON file
        prompt_path: Optional path to custom prompt file

    Returns:
        Dictionary containing detailed performance metrics as a flat structure
    """
    # Create extractor
    extractor = create_extractor(
        framework=framework, model=model, prompt_path=prompt_path
    )

    # Load SQL code
    with open(sql_file) as f:
        sql = f.read()

    # Load expected output (ground truth)
    with open(expected_json_file) as f:
        expected = json.load(f)

    # Run extraction
    result, execution_time = run_extractor_with_retry(extractor, sql, max_trials=5)
    extracted = result.to_dict()

    # Compare results and get metrics
    comparison_metrics = compare_extraction_results(extracted, expected)

    # Create final metrics dictionary with metadata
    metrics = {
        "framework": framework,
        "model": model,
        "prompt": os.path.basename(prompt_path) if prompt_path else "default",
        "sql_file": os.path.basename(sql_file),
        **comparison_metrics,
        "exec_time": execution_time,
        "extracted_result": json.dumps(extracted),
        "expected_result": json.dumps(expected),
    }

    return metrics
