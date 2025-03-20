import json
from pathlib import Path
from typing import Annotated

import typer
import yaml
from loguru import logger

from sqldeps.llm_parsers import BaseSQLExtractor, create_extractor

# Create the main Typer app
app = typer.Typer(
    name="sqldeps",
    help=(
        "SQL Dependency Extractor - "
        "Analyze SQL files to extract table and column dependencies"
    ),
    add_completion=True,
)


def extract_dependencies(
    extractor: BaseSQLExtractor, fpath: Path, recursive: bool
) -> dict:
    """Extract dependencies from a file or directory."""
    logger.info(
        f"Extracting dependencies from {'file' if fpath.is_file() else 'folder'}: "
        f"{fpath}"
    )
    dependencies = (
        extractor.extract_from_file(fpath)
        if fpath.is_file()
        else extractor.extract_from_folder(fpath, recursive=recursive)
    )
    return dependencies


def match_dependencies_against_schema(
    extractor: BaseSQLExtractor,
    dependencies: dict,
    db_target_schemas: str,
    db_credentials: Path | None,
) -> dict:
    """Match extracted dependencies against a database schema."""
    from .database import PostgreSQLConnector

    logger.info("Retrieving schema from database...")
    schemas = [s.strip() for s in db_target_schemas.split(",")]

    with open(db_credentials) as file:
        db_credentials = yaml.safe_load(file)["database"]

    conn = PostgreSQLConnector(
        host=db_credentials["host"],
        port=db_credentials["port"],
        database=db_credentials["database"],
        username=db_credentials["username"],
    )

    db_dependencies = extractor.match_database_schema(
        dependencies, db_connection=conn, target_schemas=schemas
    )
    return db_dependencies


def save_output(
    dependencies: dict, output_path: Path, is_schema_match: bool = False
) -> None:
    """Save extracted dependencies to the specified output format."""
    if output_path.suffix.lower() == ".csv":
        df_output = dependencies if is_schema_match else dependencies.to_dataframe()
        df_output.to_csv(output_path, index=False)
        logger.success(f"Saved to CSV: {output_path}")
    else:
        json_output = dependencies.to_dict()
        output_path = output_path.with_suffix(".json")
        with open(output_path, "w") as f:
            json.dump(json_output, f, indent=2)
        logger.success(f"Saved to JSON: {output_path}")


@app.command()
def main(
    fpath: Annotated[
        Path,
        typer.Argument(
            help="SQL file or directory path",
            exists=True,
            dir_okay=True,
            file_okay=True,
            resolve_path=True,
        ),
    ],
    framework: Annotated[
        str,
        typer.Option(
            help="LLM framework to use [groq, openai, deepseek]",
            case_sensitive=False,
        ),
    ] = "groq",
    model: Annotated[
        str | None, typer.Option(help="Model name for the selected framework")
    ] = None,
    prompt: Annotated[
        Path | None,
        typer.Option(
            help="Path to custom prompt YAML file",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Recursively scan folder for SQL files"),
    ] = False,
    db_match_schema: Annotated[
        bool, typer.Option(help="Match dependencies against database schema")
    ] = False,
    db_target_schemas: Annotated[
        str,
        typer.Option(help="Comma-separated list of target schemas to validate against"),
    ] = "public",
    db_credentials: Annotated[
        Path | None,
        typer.Option(
            help="Path to database credentials YAML file",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            "--output", "-o", help="Output file path for extracted dependencies"
        ),
    ] = Path("dependencies.json"),
) -> None:
    """Extract SQL dependencies from file or folder.

    This tool analyzes SQL files to identify table and column dependencies,
    optionally validating them against a real database schema.
    """
    try:
        extractor = create_extractor(
            framework=framework, model=model, prompt_path=prompt
        )
        dependencies = extract_dependencies(extractor, fpath, recursive)

        if db_match_schema:
            dependencies = match_dependencies_against_schema(
                extractor, dependencies, db_target_schemas, db_credentials
            )

        save_output(dependencies, output, is_schema_match=db_match_schema)

    except Exception as e:
        logger.error(f"Error extracting dependencies: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
