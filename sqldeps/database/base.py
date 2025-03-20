from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

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
        """Initialize database connection."""
        pass

    @abstractmethod
    def _create_engine(self, params: dict[str, Any]):
        """Create database engine with given parameters."""
        pass

    @abstractmethod
    def _load_config(self, config_path: Path | None) -> dict[str, Any]:
        """Load configuration from file."""
        pass

    @abstractmethod
    def _get_env_vars(self) -> dict[str, Any]:
        """Get environment variables for connection."""
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
        **kwargs,
    ) -> dict[str, Any]:
        """Resolve connection parameters from all sources."""
        pass

    @abstractmethod
    def get_schema(self, schemas: str | list[str] | None = None) -> pd.DataFrame:
        """Get database schema information."""
        pass

    def export_schema_csv(self, path: str) -> None:
        """Export schema to CSV file."""
        df = self.get_schema()
        df.to_csv(path, index=False)
