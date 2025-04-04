"""Base class for database connections.

This module defines the abstract base class for SQL database connections
and schema inspection.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.engine.base import Engine

load_dotenv()


class SQLBaseConnector(ABC):
    """Abstract base class for SQL database connections and schema inspection.

    Provides interface for:
    - Database connection with multiple configuration sources
    - Schema inspection and export
    - Engine-specific connection handling
    """

    @abstractmethod
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize database connection.

        Args:
            host: Database host address
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            config_path: Path to configuration file
        """
        pass

    @abstractmethod
    def _create_engine(self, params: dict[str, Any]) -> Engine:
        """Create database engine with given parameters.

        Args:
            params: Dictionary of connection parameters

        Returns:
            Database engine
        """
        pass

    @abstractmethod
    def _load_config(self, config_path: Path | None) -> dict[str, Any]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary with configuration parameters
        """
        pass

    @abstractmethod
    def _get_env_vars(self) -> dict[str, Any]:
        """Get environment variables for connection.

        Returns:
            Dictionary with environment variables
        """
        pass

    @abstractmethod
    def _resolve_params(
        self,
        host: str | None,
        port: int | None,
        database: str | None,
        username: str | None,
        password: str | None,
        config_path: Path | None,
        **kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve connection parameters from all sources.

        Args:
            host: Database host address
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            config_path: Path to configuration file
            **kwargs: Additional parameters

        Returns:
            Dictionary with resolved connection parameters
        """
        pass

    @abstractmethod
    def get_schema(self, schemas: str | list[str] | None = None) -> pd.DataFrame:
        """Get database schema information.

        Args:
            schemas: Optional schema name or list of schema names to filter results

        Returns:
            DataFrame with schema information
        """
        pass

    def export_schema_csv(
        self,
        path: str,
        schemas: str | list[str] | None = None,
    ) -> None:
        """Export schema to CSV file.

        Args:
            path: Path to output CSV file
            schemas: Optional schema name or list of schema names to filter results

        Returns:
            None
        """
        df = self.get_schema(schemas)
        df.to_csv(path, index=False)
