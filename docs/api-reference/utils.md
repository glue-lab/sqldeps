# Utils Reference

SQLDeps provides utility functions for working with SQL dependencies and database schemas.

## merge_profiles

Merges multiple `SQLProfile` objects into a single one:

```python
from sqldeps.utils import merge_profiles
from sqldeps.models import SQLProfile
```

### Function Signature

```python
def merge_profiles(analyses: list[SQLProfile]) -> SQLProfile:
    """Merges multiple SQLProfile objects into a single one."""
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `analyses` | `list[SQLProfile]` | List of SQLProfile objects to merge |

### Returns

A new `SQLProfile` object that combines all dependencies and outputs from the input profiles.

### Merging Rules

- Tables from all profiles are combined
- Columns for each table are combined
- If a wildcard (`"*"`) appears in a table's columns, it takes precedence over specific columns

### Example

```python
# Profile from query1.sql
profile1 = SQLProfile(
    dependencies={"users": ["id", "name"]},
    outputs={}
)

# Profile from query2.sql
profile2 = SQLProfile(
    dependencies={"users": ["email"], "orders": ["order_id"]},
    outputs={"report": ["user_id"]}
)

# Merge profiles
merged = merge_profiles([profile1, profile2])

# Result:
# {
#   "dependencies": {
#     "users": ["id", "name", "email"],
#     "orders": ["order_id"]
#   },
#   "outputs": {
#     "report": ["user_id"]
#   }
# }
```

## merge_schemas

Matches extracted SQL dependencies with the actual database schema:

```python
from sqldeps.utils import merge_schemas
```

### Function Signature

```python
def merge_schemas(
    df_extracted_schema: pd.DataFrame, 
    df_db_schema: pd.DataFrame
) -> pd.DataFrame:
    """Matches extracted SQL dependencies with the actual database schema."""
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `df_extracted_schema` | `pd.DataFrame` | DataFrame with extracted dependencies |
| `df_db_schema` | `pd.DataFrame` | DataFrame with actual database schema |

### Returns

A merged DataFrame with an `exact_match` flag indicating whether each dependency was found in the database schema.

### Matching Logic

The function handles several special cases:

1. **Exact schema matches**: When both schema and table match exactly
2. **Schema-agnostic matches**: When the table is found in a different schema
3. **Wildcard columns (`"*"`)**: Expanded to include all columns from the matching table(s)
4. **Tables with no columns (None)**: Matched at the table level

### Example

```python
# Extracted schema (from SQLProfile.to_dataframe())
df_extracted = pd.DataFrame([
    {"schema": "public", "table": "users", "column": "id"},
    {"schema": None, "table": "orders", "column": "*"},
])

# Actual database schema
df_db = pd.DataFrame([
    {"schema": "public", "table": "users", "column": "id", "data_type": "integer"},
    {"schema": "public", "table": "users", "column": "name", "data_type": "varchar"},
    {"schema": "sales", "table": "orders", "column": "id", "data_type": "integer"},
    {"schema": "sales", "table": "orders", "column": "amount", "data_type": "numeric"},
])

# Match schemas
result = merge_schemas(df_extracted, df_db)

# Result will include all columns with exact_match flag
```

## schema_diff

Checks if extracted schema entries exist in the database schema:

```python
from sqldeps.utils import schema_diff
```

### Function Signature

```python
def schema_diff(
    df_extracted_schema: pd.DataFrame, 
    df_db_schema: pd.DataFrame, 
    copy: bool = True
) -> pd.DataFrame:
    """Checks if extracted schema entries exist in the database schema."""
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df_extracted_schema` | `pd.DataFrame` | | Extracted table-column dependencies |
| `df_db_schema` | `pd.DataFrame` | | Actual database schema information |
| `copy` | `bool` | `True` | Whether to create a copy of the input DataFrame |

### Returns

The extracted schema DataFrame with an added `match_db` flag.

### Example

```python
# Check which entries exist in database
result = schema_diff(df_extracted, df_db)
print(result[result["match_db"]])  # Existing entries
print(result[~result["match_db"]])  # Missing entries
```

## Configuration Utilities

SQLDeps also includes a small config module:

```python
from sqldeps.config import load_config
```

### load_config

Loads configuration from a YAML file:

```python
def load_config(config_path):
    """Load configuration from a YAML file."""
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `config_path` | `str \| Path` | Path to YAML configuration file |

#### Returns

The parsed configuration as a dictionary.

#### Example

```python
# Load configuration
config = load_config("configs/database.yml")
print(config["database"]["host"])
```
