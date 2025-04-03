# Database Integration

SQLDeps provides robust database integration for matching extracted dependencies against actual database schemas.

## Supported Databases

Currently, SQLDeps supports:

- PostgreSQL (primary support)

## Database Connection

### Using the PostgreSQLConnector

The `PostgreSQLConnector` class provides a secure way to connect to PostgreSQL databases:

```python
from sqldeps.database import PostgreSQLConnector

# Create a connection using direct parameters
conn = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="mydatabase",
    username="username",
    password="password"  # Optional, can use .pgpass
)

# Alternative: load from YAML config file
conn = PostgreSQLConnector(
    config_path="path/to/database.yml"
)

# Alternative: use environment variables
# DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
conn = PostgreSQLConnector()
```

### Connection Priority

The connector uses the following priority for connection parameters:

1. Direct parameters in constructor
2. YAML config file
3. Environment variables
4. .pgpass file (for password only)

### Database Configuration YAML

```yaml
# database.yml
database:
  host: localhost
  port: 5432
  database: mydatabase
  username: username
  password: password  # Optional
```

### Environment Variables

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
DB_USER=username
DB_PASSWORD=password
```

### PostgreSQL Password File

SQLDeps supports standard PostgreSQL password file (`~/.pgpass`) format:

```
hostname:port:database:username:password
```

## Schema Retrieval

You can directly access database schema information:

```python
# Get all schemas
db_schema = conn.get_schema()

# Get specific schemas
db_schema = conn.get_schema(schemas=["public", "sales"])

# Export schema to CSV
conn.export_schema_csv("schema.csv")
```

## Schema Matching

### Using the API

```python
from sqldeps.llm_parsers import create_extractor
from sqldeps.database import PostgreSQLConnector

# Create extractor and extract dependencies
extractor = create_extractor()
dependencies = extractor.extract_from_file("query.sql")

# Connect to database
conn = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="mydatabase",
    username="username"
)

# Match extracted dependencies against database schema
matching_results = extractor.match_database_schema(
    dependencies,
    db_connection=conn,
    target_schemas=["public", "sales"]
)

# Analyze database-matching results
exact_matches = matching_results[matching_results["exact_match"]]
agnostic_matches = matching_results[~matching_results["exact_match"]]

print(f"Found {len(exact_matches)} exact matches.")
print(f"Found {len(agnostic_matches)} schema-agnostic matches.")
```

### Using the CLI

```bash
sqldeps extract path/to/query.sql \
    --db-match-schema \
    --db-target-schemas public,sales \
    --db-credentials configs/database.yml \
    -o db_matching_results.csv
```

## Matching Results

The matching results are returned as a pandas DataFrame with these columns:

| Column | Description |
|--------|-------------|
| `schema` | Database schema name |
| `table` | Table name |
| `column` | Column name |
| `data_type` | Database data type |
| `exact_match` | Boolean indicating if schema name matched exactly |

### Interpreting Results

- `exact_match=True`: The table/column was found in the specified schema
- `exact_match=False`: The table/column does not have a specified schema
- Missing entries: Dependencies that weren't found in the database

## Using Schema Information in Applications

The schema matching results can be used to:

1. Identify missing dependencies before executing SQL
2. Generate data type-aware documentation
3. Create migration scripts
4. Highlight potential issues in SQL queries
5. Ensure referential integrity across schemas

## Security Considerations

SQLDeps follows security best practices for database connections:

- No hardcoded credentials in code
- Support for PostgreSQL password file
- Environment variable support
- Secure parameter handling (parameters are cleared after use)
- Connection timeouts to prevent hanging
