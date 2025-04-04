"""Base classes for LLM parsers.

This module defines the abstract base class for all LLM-based SQL parsers,
providing a common interface and shared functionality.
"""

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

from sqldeps.cache import cleanup_cache, load_from_cache, save_to_cache
from sqldeps.database.base import SQLBaseConnector
from sqldeps.models import SQLProfile
from sqldeps.rate_limiter import RateLimiter
from sqldeps.utils import find_sql_files, merge_profiles, merge_schemas


class BaseSQLExtractor(ABC):
    """Mandatory interface for all parsers.

    Attributes:
        VALID_EXTENSIONS: Set of valid file extensions to process
        framework: Name of the LLM framework being used
        model: Name of the specific model
        prompt_path: Path to custom prompt file
        params: Additional parameters for the LLM
        prompts: Loaded prompt templates
    """

    VALID_EXTENSIONS: ClassVar[set[str]] = {"sql"}

    @abstractmethod
    def __init__(
        self, model: str, params: dict | None = None, prompt_path: Path | None = None
    ) -> None:
        """Initialize with model name and vendor-specific params.

        Args:
            model: Name of the LLM model to use
            params: Additional parameters for the LLM API
            prompt_path: Path to custom prompt YAML file
        """
        self.framework = self.__class__.__name__.replace("Extractor", "").lower()
        self.model = model
        self.prompt_path = prompt_path
        self.params = params or {}
        self.prompts = self._load_prompts(prompt_path)

        # Set default temperature to 0 in case it's not specified (fails for OpenAI o3)
        if "temperature" not in self.params:
            self.params["temperature"] = 0

    def extract_from_query(self, sql: str) -> SQLProfile:
        """Core extraction method.

        Args:
            sql: SQL query string to analyze

        Returns:
            SQLProfile object containing dependencies and outputs

        Raises:
            ValueError: If response cannot be processed
        """
        formatted_sql = sqlparse.format(sql, reindent=True, keyword_case="upper")
        prompt = self._generate_prompt(formatted_sql)
        response = self._query_llm(prompt)
        self.last_response = response
        return self._process_response(response)

    def extract_from_file(self, file_path: str | Path) -> SQLProfile:
        """Extract dependencies from a SQL file.

        Args:
            file_path: Path to SQL file

        Returns:
            SQLProfile object containing dependencies and outputs

        Raises:
            FileNotFoundError: If file does not exist
        """
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
        merge_sql_profiles: bool = False,
        valid_extensions: set[str] | None = None,
        n_workers: int = 1,
        rpm: int = 100,
        use_cache: bool = True,
        clear_cache: bool = False,
    ) -> SQLProfile | dict[str, SQLProfile]:
        """Extract and merge dependencies from all SQL files in a folder.

        Args:
            folder_path: Path to folder containing SQL files
            recursive: Whether to search recursively
            merge_sql_profiles: Whether to merge all results into a single SQLProfile
            valid_extensions: Set of valid file extensions to process
            n_workers: Number of worker processes for parallel execution
            rpm: Maximum requests per minute for API rate limiting
            use_cache: Whether to use cached results
            clear_cache: Whether to clear the cache after processing

        Returns:
            SQLProfile object or dictionary mapping file paths to SQLProfile objects

        Raises:
            ValueError: If no dependencies could be extracted
        """
        # Find all SQL files
        sql_files = find_sql_files(folder_path, recursive, valid_extensions)

        # Choose processing strategy based on n_workers
        if n_workers != 1:
            # Parallel processing
            dependencies = self._process_files_in_parallel(
                sql_files, n_workers=n_workers, rpm=rpm, use_cache=use_cache
            )
        else:
            # Sequential processing
            dependencies = self._process_files_sequentially(
                sql_files, rpm=rpm, use_cache=use_cache
            )

        # If no results were extracted
        if not dependencies:
            raise ValueError("No dependencies could be extracted from any SQL file")

        # Clean up cache if requested - now handled in one place
        if clear_cache and use_cache:
            cleanup_cache()

        # Merge results if requested - now handled in one place
        if merge_sql_profiles:
            return merge_profiles(list(dependencies.values()))

        return dependencies

    def _process_files_sequentially(
        self, sql_files: list[Path], rpm: int = 100, use_cache: bool = True
    ) -> dict[str, SQLProfile]:
        """Process a list of SQL files sequentially with rate limiting.

        Args:
            sql_files: List of SQL file paths to process
            rpm: Requests per minute limit
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping file paths to their respective SQLProfile objects

        Raises:
            ValueError: If no dependencies could be extracted
        """
        # Create rate limiter
        rate_limiter = RateLimiter(rpm)
        dependencies = {}

        # Log about cache and rate limiting
        if use_cache:
            logger.info("Cache usage: enabled")
        logger.info(
            f"Processing {len(sql_files)} SQL files sequentially"
            + (f" with RPM: {rpm}" if rpm > 0 else "")
        )

        # Process each file with rate limiting
        for sql_file in tqdm(sql_files, desc="Processing SQL files"):
            try:
                # Check cache first if enabled
                if use_cache:
                    result = load_from_cache(sql_file)
                    if result:
                        dependencies[str(sql_file)] = result
                        continue

                # Apply rate limiting
                rate_limiter.wait_if_needed()

                # Extract dependencies
                result = self.extract_from_file(sql_file)
                dependencies[str(sql_file)] = result

                # Save to cache if enabled
                if use_cache:
                    save_to_cache(result, sql_file)

            except Exception as e:
                logger.warning(f"Failed to process {sql_file}: {e}")
                continue

        # If no results were extracted
        if not dependencies:
            raise ValueError("No dependencies could be extracted from any SQL file")

        return dependencies

    def _process_files_in_parallel(
        self,
        sql_files: list[Path],
        n_workers: int = 2,
        rpm: int = 100,
        use_cache: bool = True,
    ) -> dict[str, SQLProfile]:
        """Process a list of SQL files in parallel with rate limiting.

        Args:
            sql_files: List of SQL file paths to process
            n_workers: Number of worker processes
            rpm: Requests per minute limit
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping file paths to their respective SQLProfile objects
        """
        from sqldeps.parallel import process_files_in_parallel

        return process_files_in_parallel(
            sql_files,
            framework=self.framework,
            model=self.model,
            prompt_path=self.prompt_path,
            n_workers=n_workers,
            rpm=rpm,
            use_cache=use_cache,
        )

    def match_database_schema(
        self,
        dependencies: SQLProfile,
        db_connection: SQLBaseConnector,
        target_schemas: list[str] | None = None,
    ) -> pd.DataFrame:
        """Match extracted dependencies against actual database schema.

        Args:
            dependencies:SQLDependency object containing tables and columns to match
            db_connection: Database connector instance to use for schema validation
            target_schemas: Optional list of database schemas to validate against
                (default: ["public"])

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
        """Load prompts from a YAML file.

        Args:
            path: Path to prompt YAML file

        Returns:
            Dictionary with loaded prompts

        Raises:
            ValueError: If required keys are missing from prompt file
        """
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
        """Generate the prompt for the LLM.

        Args:
            sql: SQL query to analyze

        Returns:
            Formatted prompt string
        """
        return self.prompts["user_prompt"].format(sql=sql)

    @abstractmethod
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM with the generated prompt to generate a response.

        Args:
            prompt: Prompt to send to the LLM

        Returns:
            Response from the LLM
        """

    def _process_response(self, response: str) -> SQLProfile:
        """Process the LLM response into a SQLProfile object.

        Args:
            response: Response from the LLM

        Returns:
            SQLProfile object with dependencies and outputs

        Raises:
            ValueError: If JSON cannot be decoded or required keys are missing
        """
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
        """Normalize extensions by ensuring they are lowercase without leading dots.

        Args:
            extensions: Set of file extensions

        Returns:
            Normalized set of file extensions
        """
        if extensions:
            return {ext.lstrip(".").lower() for ext in extensions}
        return BaseSQLExtractor.VALID_EXTENSIONS
