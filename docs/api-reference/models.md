# Models Reference

## SQLProfile

The core data model of SQLDeps is the `SQLProfile` class, which stores information about SQL dependencies and outputs.

```python
from sqldeps.models import SQLProfile
```

### Class Definition

```python
@dataclass
class SQLProfile:
    """Data class to hold both SQL dependencies and outputs."""

    # Dependencies (input tables/columns required by the query)
    dependencies: dict[str, list[str]]  # {table_name: [column_names]}

    # Outputs (tables/columns created or modified by the query)
    outputs: dict[str, list[str]]  # {table_name: [column_names]}
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `dependencies` | `dict[str, list[str]]` | Dictionary mapping table names to lists of column names that are required by the SQL query |
| `outputs` | `dict[str, list[str]]` | Dictionary mapping table names to lists of column names that are created or modified by the SQL query |
| `dependency_tables` | `list[str]` | List of all table names referenced as dependencies |
| `outcome_tables` | `list[str]` | List of all table names referenced as outputs |

### Methods

#### `to_dict()`

Converts the `SQLProfile` to a dictionary format.

```python
def to_dict(self) -> dict:
    """Convert to dictionary format."""
    return {"dependencies": self.dependencies, "outputs": self.outputs}
```

#### `to_dataframe()`

Converts the `SQLProfile` to a pandas DataFrame.

```python
def to_dataframe(self) -> pd.DataFrame:
    """Convert to a DataFrame with type column indicating dependency or outcome."""
    # Returns DataFrame with columns: type, schema, table, column
```

### Usage Example

```python
# Create a SQLProfile object
profile = SQLProfile(
    dependencies={
        "users": ["id", "name", "status"],
        "orders": ["order_id", "user_id"]
    },
    outputs={
        "order_summary": ["user_id", "total_orders"]
    }
)

# Access properties
print(profile.dependency_tables)  # ['orders', 'users']
print(profile.outcome_tables)     # ['order_summary']

# Convert to dictionary
profile_dict = profile.to_dict()
print(profile_dict)

# Convert to DataFrame
profile_df = profile.to_dataframe()
print(profile_df)
```

## Handling Schema Qualifiers

SQLDeps preserves schema-qualified table names exactly as they appear in the SQL query:

```python
# Schema-qualified example
profile = SQLProfile(
    dependencies={
        "public.users": ["id", "name"],
        "sales.orders": ["order_id", "user_id"]
    },
    outputs={
        "reports.summary": ["user_id", "total"]
    }
)
```

In the resulting DataFrame, schema and table names are split into separate columns:

```
      type  schema    table   column
0 dependency public    users       id
1 dependency public    users     name
2 dependency  sales   orders order_id
3 dependency  sales   orders  user_id
4    outcome reports summary   user_id
5    outcome reports summary     total
```

## Special Column Values

SQLDeps uses some special values in column lists:

- `"*"`: Indicates all columns in a table (e.g., from `SELECT *`)
- `[]` (empty list): Indicates a table reference without specific columns (e.g., from `TRUNCATE TABLE`)
- `None`: Used in the DataFrame representation for table-level references

## Related Functions

In the `utils` module, several functions work with `SQLProfile` objects:

- `merge_profiles()`: Combines multiple `SQLProfile` objects
- `merge_schemas()`: Matches extracted dependencies against actual database schemas
- `schema_diff()`: Compares extracted dependencies with database schemas
