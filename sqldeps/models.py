"""Data models for SQLDeps.

This module defines the core data structures used by SQLDeps for
representing SQL dependencies and outputs.
"""

from dataclasses import dataclass

import pandas as pd


SQLProfileDataModel = dict[str, dict[str, dict[str | list[str]]]]


@dataclass
class SQLProfile:
    """Data class to hold both SQL dependencies and outputs."""

    # Dependencies (input tables/columns required by the query)
    dependencies: SQLProfileDataModel

    # Outputs (tables/columns created or modified by the query)
    outputs: SQLProfileDataModel

    def _sort_column_names(self, data: SQLProfileDataModel) -> None:
        """Sort column names in place for data of type SQLProfileDataModel."""
        for mode, objs in data.items():
            for obj, info in objs.items():
                if info["type"] == "table":
                    info["columns"].sort()

    def __post_init__(self) -> None:
        """Sort column names for consistent output."""
        self._sort_column_names(self.dependencies)
        self._sort_column_names(self.outputs)

    def _sorted_table_names(self, data: SQLProfileDataModel) -> list[str]:
        """Get a sorted list of tables from data of type SQLProfileDataModel."""
        tables = []
        if "run" in data:
            run_objs = data["run"]
            tables = [
                obj_name for obj_name, obj_info in run_objs
                if obj_info["type"] == "table"
            ]  
        return sorted(tables)       

    @property
    def dependency_tables(self) -> list[str]:
        """Get list of tables that are run dependencies.

        Returns:
            list[str]: Sorted list of table names referenced as dependencies
        """
        return _sorted_table_names(self.dependencies)

    @property
    def outcome_tables(self) -> list[str]:
        """Get list of tables that are run outputs.

        Returns:
            list[str]: Sorted list of table names referenced as outputs
        """
        return _sorted_table_names(self.outputs)

    def to_dict(self) -> dict:
        """Convert to dictionary format.

        Returns:
            dict: Dictionary with dependencies and outputs
        """
        return {"dependencies": self.dependencies, "outputs": self.outputs}

    def _add_records_for(self, model_type: str, records: list, data: SQLProfileDataModel) -> None:
        """Add records from data in place to a running list."""
        for mode, objs in self.dependencies.items():
            for obj_name, obj_info in objs.items():
                obj_schema, obj_name = obj_name.split(".") if "." in obj_name else (None, obj_name)
                records.append(
                    {
                        "type": model_type,
                        "mode": mode,
                        "schema": obj_schema,
                        "table": None,
                        "object_name": obj_name,
                        "object_type": obj_info["type"],
                    }
                )
                if "columns" in obj_info and len(obj_info["columns"]) > 0:
                    for column in obj_info["columns"]:
                        records.append(
                            {
                                "type": model_type,
                                "mode": mode,
                                "schema": schema,
                                "table": obj_name,
                                "object_name": column,
                                "object_type": "column",
                            }
                        )        

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to a DataFrame with type column indicating dependency or outcome.

        Returns:
            pd.DataFrame: DataFrame with columns for model type, schema, table, object name, and object type
        """
        records = []
        self._add_records_for("dependency", records, self.dependencies)
        self._add_records_for("outcome", records, self.outputs)
        return pd.DataFrame(records)
