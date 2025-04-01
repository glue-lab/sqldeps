"""Database connectors for SQLDeps.

This package provides database connectors for schema retrieval and validation.
"""

from .postgresql import PostgreSQLConnector

__all__ = ["PostgreSQLConnector"]
