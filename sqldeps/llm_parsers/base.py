import importlib.resources as pkg_resources
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import pandas as pd
import sqlparse
import yaml
from loguru import logger
from tqdm import tqdm

from sqldeps.database.base import SQLBaseConnector
from sqldeps.models import SQLProfile
from sqldeps.utils import merge_profiles, merge_schemas


class BaseSQLExtractor(ABC):
    """Mandatory interface for all parsers."""

    VALID_EXTENSIONS: ClassVar[set[str]] = {"sql"}

    @abstractmethod
    def __init__(
        self, model: str, params: dict | None = None, prompt_path: Path | None = None
    ) -> None:
        """Initialize with model name and vendor-specific params."""
        self.model = model
        self.params = params or {}
        self.prompts = self._load_prompts(prompt_path)

        # Set default temperature to 0 in case it's not specified
        if "temperature" not in self.params:
            self.params["temperature"] = 0

    def extract_from_query(self, sql: str) -> SQLProfile:
        """Core extraction method."""
        formatted_sql = sqlparse.format(sql, reindent=True, keyword_case="upper")
        prompt = self._generate_prompt(formatted_sql)
        response = self._query_llm(prompt)
        self.last_response = response
        return self._process_response(response)

    def extract_from_file(self, file_path: str | Path) -> SQLProfile:
        """Extract dependencies from a SQL file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")

        with open(file_path) as f:
            sql = f.read()

        return self.extract_from_query(sql)

    def extract_from_folder(
        self,
        folder_path: str | Path,
        recursive: bool = False,
        valid_extensions: set[str] | None = None,
    ) -> SQLProfile:
        """Extract and merge dependencies from all SQL files in a folder."""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        if not folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")

        # Get all files with valid extensions
        valid_extensions = self._normalize_extensions(valid_extensions)

        sql_files = [
            f
            for f in (folder_path.rglob("*") if recursive else folder_path.glob("*"))
            if f.suffix.lower().lstrip(".") in valid_extensions
        ]

        if not sql_files:
            raise ValueError(f"No SQL files found in: {folder_path}")

        # Extract dependencies from each file
        dependencies = []
        for sql_file in tqdm(sql_files):
            try:
                dep = self.extract_from_file(sql_file)
                dependencies.append(dep)
            except Exception as e:
                logger.warning(f"Failed to process {sql_file}: {e}")
                continue

        # Merge all dependencies
        return merge_profiles(dependencies)

    def match_database_schema(
        self,
        dependencies: SQLProfile,
        db_connection: SQLBaseConnector,
        target_schemas: list[str] | None = None,
    ) -> pd.DataFrame:
        """Match extracted dependencies against actual database schema.

        Args:
            dependencies: SQLDependency object containing tables and columns to match
            db_connection: Database connector instance to use for schema validation
            target_schemas: Optional list of database schemas to validate against
            (default: ['public'])

        Returns:
            pd.DataFrame: Merged schema DataFrame with validation information
        """
        # Get schema from the provided connection
        target_schemas = target_schemas or ["public"]
        db_schema = db_connection.get_schema(schemas=target_schemas)

        # Convert dependencies to DataFrame
        extracted_schema = dependencies.to_dataframe()

        # Match schemas
        return merge_schemas(extracted_schema, db_schema)

    def _load_prompts(self, path: Path | None = None) -> dict:
        """Load prompts from a YAML file."""
        if path is None:
            with (
                pkg_resources.files("sqldeps.configs.prompts")
                .joinpath("default.yml")
                .open("r") as f
            ):
                prompts = yaml.safe_load(f)
        else:
            with open(path) as f:
                prompts = yaml.safe_load(f)

        required_keys = {"user_prompt", "system_prompt"}
        if not all(key in prompts for key in required_keys):
            raise ValueError(
                f"Prompt file must contain all required keys: {required_keys}"
            )

        return prompts

    def _generate_prompt(self, sql: str) -> str:
        """Generate the prompt for the LLM."""
        return self.prompts["user_prompt"].format(sql=sql)

    @abstractmethod
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the generated prompt to generate a response."""

    def _process_response(self, response: str) -> SQLProfile:
        """Process the LLM response into a SQLProfile object."""
        try:
            # Convert result into a dictionary
            result = json.loads(response)

            if "dependencies" not in result or "outputs" not in result:
                raise ValueError(
                    "Missing required keys ('dependencies', 'outputs') in the response."
                )

            # Convert dictionary to SQLProfile
            return SQLProfile(
                dependencies=result["dependencies"], outputs=result["outputs"]
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode JSON: {e}\nResponse: {response}")

    @staticmethod
    def _normalize_extensions(extensions: set[str] | None) -> set[str]:
        """Normalize extensions by ensuring they are lowercase without leading dots."""
        if extensions:
            return {ext.lstrip(".").lower() for ext in extensions}
        return BaseSQLExtractor.VALID_EXTENSIONS
