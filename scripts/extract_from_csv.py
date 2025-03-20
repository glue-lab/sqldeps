from pathlib import Path

import pandas as pd
import typer
from loguru import logger
from tqdm import tqdm

from sqldeps.llm_parsers import create_extractor


def main(
    csv_input_path: Path = typer.Argument(
        ..., help="Input CSV file path", exists=True, dir_okay=False, resolve_path=True
    ),
    framework: str | None = typer.Option(
        "groq", help="LLM framework to use [groq, openai, deepseek]"
    ),
    model: str | None = typer.Option(None, help="Model name for selected framework"),
    prompt: Path | None = typer.Option(
        None,
        help="Path to custom prompt YAML file",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    csv_output_path: Path | None = typer.Option(
        Path("sql_dependencies.csv"), help="Output CSV file path"
    ),
    sql_input_col: str | None = typer.Option(
        "function_def", help="Existing column containing SQL queries"
    ),
    sql_output_col: str | None = typer.Option(
        "sqldeps", help="New column to store dependencies"
    ),
    maximum_rows: int | None = typer.Option(
        None, help="Maximum number of rows to process (None for all)"
    ),
) -> None:
    """Extract SQL dependencies from a CSV file containing SQL queries"""
    try:
        # Initialize extractor
        extractor = create_extractor(framework, model, prompt_path=prompt)
        logger.info(
            f"Processing {csv_input_path} using {framework.title()} "
            f"and {extractor.model}"
        )

        # Read and optionally sample data with first rows
        df = pd.read_csv(csv_input_path)
        if maximum_rows:
            df = df.head(maximum_rows)
            logger.info(f"Using first {maximum_rows} rows")

        # Extract dependencies
        tqdm.pandas(desc="Processing SQL queries")
        df[sql_output_col] = df[sql_input_col].progress_apply(
            lambda x: extractor.extract_from_query(x).to_dict()
        )
        # Save results
        df.to_csv(csv_output_path, index=False)
        logger.success(f"Results saved to {csv_output_path}")

    except Exception:
        logger.exception("Processing failed")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(main)
