import json
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
import yaml
from loguru import logger

from sqldeps import __version__
from sqldeps.cache import cleanup_cache
from sqldeps.llm_parsers import BaseSQLExtractor, create_extractor

# Main Typer app and subcommands
app = typer.Typer(
    name="sqldeps",
    help=(
        "SQL Dependency Extractor - "
        "Analyze SQL files to extract table and column dependencies"
    ),
    add_completion=True,
)

# Create subcommands
app_cmd = typer.Typer(help="Run the SQLDeps web application")
cache_cmd = typer.Typer(help="Manage SQLDeps cache")

# Add subcommand groups to main app
app.add_typer(app_cmd, name="app")
app.add_typer(cache_cmd, name="cache")


def extract_dependencies(
    extractor: BaseSQLExtractor,
    fpath: Path,
    recursive: bool,
    n_workers: int = 1,
    rpm: int = 100,
    use_cache: bool = True,
    clear_cache: bool = False,
) -> dict:
    """Extract dependencies from a file or directory."""
    logger.info(
        f"Extracting dependencies from {'file' if fpath.is_file() else 'folder'}: "
        f"{fpath}"
    )
    if fpath.is_file():
        return extractor.extract_from_file(fpath)
    else:
        return extractor.extract_from_folder(
            fpath,
            recursive=recursive,
            n_workers=n_workers,
            rpm=rpm,
            use_cache=use_cache,
            clear_cache=clear_cache,
        )


def match_dependencies_against_schema(
    extractor: BaseSQLExtractor,
    dependencies: dict,
    db_target_schemas: str,
    db_credentials: Path | None,
    db_dialect: str = "postgresql",
) -> dict:
    """Match extracted dependencies against a database schema."""
    if db_dialect.lower() == "postgresql":
        from .database import PostgreSQLConnector as DBConnector
    else:
        raise ValueError(f"Unsupported database dialect: {db_dialect}")

    logger.info("Retrieving schema from database...")
    schemas = [s.strip() for s in db_target_schemas.split(",")]

    with open(db_credentials) as file:
        db_credentials = yaml.safe_load(file)["database"]

    conn = DBConnector(
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


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"SQLDeps version: {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version", help="Show the version and exit.", callback=version_callback
        ),
    ] = False,
):
    """SQL Dependency Extractor.

    Analyze SQL files to extract table and column dependencies.
    """
    pass


def path_complete(incomplete: str):
    """Simple path completion."""
    for path in Path(".").glob(f"{incomplete}*"):
        if path.is_dir():
            yield f"{path.name}/"
        else:
            yield path.name


@app.command()
def extract(
    fpath: Annotated[
        Path,
        typer.Argument(
            help="SQL file or directory path",
            exists=True,
            dir_okay=True,
            file_okay=True,
            resolve_path=True,
            autocompletion=path_complete,
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
    db_dialect: Annotated[
        str,
        typer.Option(
            help="Database dialect to use for schema validation",
            case_sensitive=False,
        ),
    ] = "postgresql",
    n_workers: Annotated[
        int,
        typer.Option(
            help=(
                "Number of workers for parallel processing. "
                "Use -1 for all CPU cores, 1 for sequential processing."
            ),
        ),
    ] = 1,
    rpm: Annotated[
        int,
        typer.Option(
            help="Maximum requests per minute for API rate limiting (0 to disable)",
        ),
    ] = 100,
    use_cache: Annotated[
        bool,
        typer.Option(help="Use local cache for SQL extraction results"),
    ] = True,
    clear_cache: Annotated[
        bool,
        typer.Option(help="Clear local cache after processing"),
    ] = False,
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

        dependencies = extract_dependencies(
            extractor,
            fpath,
            recursive=recursive,
            n_workers=n_workers,
            rpm=rpm,
            use_cache=use_cache,
            clear_cache=clear_cache,
        )

        if db_match_schema:
            dependencies = match_dependencies_against_schema(
                extractor, dependencies, db_target_schemas, db_credentials, db_dialect
            )

        save_output(dependencies, output, is_schema_match=db_match_schema)

    except Exception as e:
        logger.error(f"Error extracting dependencies: {e}")
        raise typer.Exit(code=1)


# App subcommand
@app_cmd.callback(invoke_without_command=True)
def app_main():
    """Run SQLDeps web application."""
    try:
        # Get the path to the app module in the package
        package_dir = Path(__file__).parent
        app_module_path = package_dir / "app" / "main.py"

        if not app_module_path.exists():
            raise FileNotFoundError("App not found in package")

        logger.info(f"Running web application from: {app_module_path}")

        # Run streamlit with the app module
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_module_path)])
    except Exception as e:
        logger.error(f"Failed to start web application: {e}")
        raise typer.Exit(code=1)


# Cache subcommands
@cache_cmd.command("clear")
def cache_clear():
    """Clear the SQLDeps cache directory."""
    try:
        logger.info("Clearing SQLDeps cache...")
        success = cleanup_cache()
        if success:
            logger.success("Cache cleared successfully")
        else:
            logger.error("Failed to clear cache")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
