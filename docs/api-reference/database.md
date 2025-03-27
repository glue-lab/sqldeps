# Database Reference

SQLDeps provides database connectivity for schema validation through its database module.

## SQLBaseConnector

The abstract base class that defines the interface for all database connectors:

```python
from sqldeps.database.base import SQLBaseConnector
```

### Abstract Methods

| Method | Description |
|--------|-------------|
| `__init__()` | Initialize database connection |
| `_create_engine()` | Create database engine with given parameters |
| `_load_config()` | Load configuration from file |
| `_get_env_vars()` | Get environment variables for connection |
| `_resolve_params()` | Resolve connection parameters from all sources |
| `get_schema()` | Get database schema information |

### Concrete Methods

| Method | Description |
|--------|-------------|
| `export_schema_csv()` | Export schema to CSV file |

## PostgreSQLConnector

The primary database connector implementation for PostgreSQL:

```python
from sqldeps.database import PostgreSQLConnector
```

### Initialization

```python
def __init__(
    self,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    username: str | None = None,
    password: str | None = None,
    config_path: Path | None = None,
) -> None:
    """Initialize database connection with provided configuration."""
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str \| None` | `None` | Database host address |
| `port` | `int \| None` | `None` | Database port |
| `database` | `str \| None` | `None` | Database name |
| `username` | `str \| None` | `None` | Database username |
| `password` | `str \| None` | `None` | Database password |
| `config_path` | `Path \| None` | `None` | Path to YAML config file |

### Method: `get_schema()`

Retrieves database schema information:

```python
def get_schema(self, schemas: str | list[str] | None = None) -> pd.DataFrame:
    """Retrieve database schema information as a DataFrame."""
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schemas` | `str \| list[str] \| None` | `None` | Optional schema name or list of schema names to filter results |

#### Returns

A pandas DataFrame with columns: `schema`, `table`, `column`, `data_type`

### Method: `export_schema_csv()`

Exports schema information to a CSV file:

```python
def export_schema_csv(
    self,
    path: str,
    schemas: str | list[str] | None = None,
) -> None:
    """Export schema to CSV file."""
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Path to the output CSV file |
| `schemas` | `str \| list[str] \| None` | Optional schema name or list of schema names to filter results |

### Connection Configuration

The `PostgreSQLConnector` supports multiple configuration sources:

1. **Direct parameters** in constructor

2. **YAML configuration file**:
   ```yaml
   # database.yml
   database:
     host: localhost
     port: 5432
     database: mydatabase
     username: username
     password: password
   ```

3. **Environment variables**:

    - `DB_HOST`
    - `DB_PORT`
    - `DB_NAME`
    - `DB_USER`
    - `DB_PASSWORD`

4. **PostgreSQL password file** (`~/.pgpass`): The connector will automatically check 
this file for matching credentials if no password is provided through other methods.
The file format should follow PostgreSQL standards with each line containing:

```bash
hostname:port:database:username:password
```

where wildcards (*) can be used to match multiple values.

### Usage Examples

#### Basic Connection

```python
# Connect using direct parameters
conn = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="mydatabase",
    username="username",
    password="password"
)

# Connect using YAML configuration
conn = PostgreSQLConnector(
    config_path=Path("configs/database.yml")
)

# Connect using environment variables
# Assumes DB_HOST, DB_NAME, etc. are set
conn = PostgreSQLConnector()
```

#### Getting Schema Information

```python
# Get all schemas
all_schemas = conn.get_schema()

# Get specific schemas
specific_schemas = conn.get_schema(schemas=["public", "sales"])

# Export schema to CSV
conn.export_schema_csv("database_schema.csv")
```

#### Using with Schema Validation

```python
from sqldeps.llm_parsers import create_extractor

# Create extractor and analyze SQL
extractor = create_extractor()
dependencies = extractor.extract_from_file("query.sql")

# Connect to database
conn = PostgreSQLConnector(
    host="localhost",
    database="mydatabase",
    username="username"
)

# Validate dependencies against schema
validated_schema = extractor.match_database_schema(
    dependencies,
    db_connection=conn,
    target_schemas=["public", "sales"]
)

print(validated_schema)
```
