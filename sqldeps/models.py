"""Data models for SQLDeps.

This module defines the core data structures used by SQLDeps for
representing SQL dependencies and outputs.
"""

from dataclasses import dataclass

import pandas as pd


FUNC_TYPE_LITERAL = ":function"


@dataclass
class SQLProfile:
    """Data class to hold both SQL dependencies and outputs."""

    # Dependencies (input tables/columns required by the query)
    dependencies: dict[str, list[str] | str]

    # Outputs (tables/columns created or modified by the query)
    outputs: dict[str, list[str]]

    def __post_init__(self) -> None:
        """Sort tables and columns for consistent output."""
        self.dependencies = {
            table: FUNC_TYPE_LITERAL if cols == FUNC_TYPE_LITERAL else sorted(set(cols))
            for table, cols in sorted(self.dependencies.items())
        }
        self.outputs = {
            table: FUNC_TYPE_LITERAL if cols == FUNC_TYPE_LITERAL else sorted(set(cols))
            for table, cols in sorted(self.outputs.items())
        }

    @property
    def dependency_tables(self) -> list[str]:
        """Get list of dependency tables.

        Returns:
            list[str]: Sorted list of table names referenced as dependencies
        """
        return sorted(self.dependencies.keys())

    @property
    def outcome_tables(self) -> list[str]:
        """Get list of outcome tables.

        Returns:
            list[str]: Sorted list of table names referenced as outputs
        """
        return sorted(self.outputs.keys())

    def to_dict(self) -> dict:
        """Convert to dictionary format.

        Returns:
            dict: Dictionary with dependencies and outputs
        """
        return {"dependencies": self.dependencies, "outputs": self.outputs}

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to a DataFrame with type column indicating dependency or outcome.

        Returns:
            pd.DataFrame: DataFrame with columns for type, schema, table, and column
        """
        records = []

        # Add dependencies
        for table, columns in self.dependencies.items():
            schema, table_name = table.split(".") if "." in table else (None, table)
            if columns and columns != FUNC_TYPE_LITERAL:
                for column in columns:
                    records.append(
                        {
                            "type": "dependency",
                            "schema": schema,
                            "table": table_name,
                            "column": column,
                        }
                    )
            elif columns and columns == FUNC_TYPE_LITERAL:
                records.append(
                    {
                        "type": "dependency",
                        "schema": schema,
                        "table": table_name,
                        "column": FUNC_TYPE_LITERAL,
                    }
                )
            else:
                records.append(
                    {
                        "type": "dependency",
                        "schema": schema,
                        "table": table_name,
                        "column": None,
                    }
                )

        # Add outputs
        for table, columns in self.outputs.items():
            schema, table_name = table.split(".") if "." in table else (None, table)
            if columns and columns != FUNC_TYPE_LITERAL:
                for column in columns:
                    records.append(
                        {
                            "type": "outcome",
                            "schema": schema,
                            "table": table_name,
                            "column": column,
                        }
                    )
            elif columns and columns == FUNC_TYPE_LITERAL:
                records.append(
                    {
                        "type": "outcome",
                        "schema": schema,
                        "table": table_name,
                        "column": FUNC_TYPE_LITERAL,
                    }
                )
            else:
                records.append(
                    {
                        "type": "outcome",
                        "schema": schema,
                        "table": table_name,
                        "column": None,
                    }
                )

        return pd.DataFrame(records)
