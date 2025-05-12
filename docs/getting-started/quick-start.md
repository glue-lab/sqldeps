# Quick Start

SQLDeps provides both API and CLI interfaces for extracting dependencies from SQL queries.

## API Usage

```python
from sqldeps.llm_parsers import create_extractor

# Create extractor with default settings (framework="litellm", model="openai/gpt-4.1")
extractor = create_extractor()

# Extract dependencies and outputs from a SQL query
sql_query = """
WITH user_orders AS (
    SELECT o.user_id, COUNT(*) AS order_count
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE u.status = 'active'
    GROUP BY o.user_id
)

CREATE TABLE transactions.user_order_summary AS
SELECT * FROM user_orders;
"""
result = extractor.extract_from_query(sql_query)

# Print the results
print("Dependencies:")
print(result.dependencies)
print("\nOutputs:")
print(result.outputs)

# Or extract from a file
result = extractor.extract_from_file('path/to/query.sql')

# Convert to dictionary or DataFrame
dict_format = result.to_dict()
df_format = result.to_dataframe()
```

## CLI Usage

```bash
# Basic example with default settings
sqldeps extract path/to/query.sql

# Specify framework and output format
sqldeps extract path/to/query.sql --framework=litellm --model=gpt-4.1-mini -o results.json

# Scan a folder recursively with intelligent parallelization
sqldeps extract \
    data/sql_folder \       # Automatically detect if path is file or folder       
    --recursive \           # Scan folder recursively
    --framework=deepseek \  # Specify framework/provider
    --rpm 50                # Maximum 50 requests per minute
    --n-workers -1 \        # Use all available processors
    -o results.csv          # Output a dataframe as CSV instead of JSON
```

```bash
# Get help on available commands
sqldeps --help

# Get help on extract - the main command
sqldeps extract --help
```

## Web Application

SQLDeps includes a Streamlit-based web interface:

```bash
# Run the web app
sqldeps app
```

**Note**: The web application is designed for single-file extraction and demonstration purposes. For processing multiple files or entire folders, use the API or CLI instead.

## Example

Given this SQL query:

```sql
-- Common Table Expression (CTE) to count user orders for active users
WITH user_orders AS (
    SELECT o.user_id, COUNT(*) AS order_count
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE u.status = 'active'
    GROUP BY o.user_id
)

-- Create a new table from the CTE
CREATE TABLE transactions.user_order_summary AS
SELECT * FROM user_orders;
```

SQLDeps will extract:

```json
{
  "dependencies": {
    "orders": ["user_id"],
    "users": ["id", "status"]
  },
  "outputs": {
    "transactions.user_order_summary": ["*"]
  }
}
```

Notice how:

- CTE (`user_orders`) is correctly excluded
- Real source tables (`orders`, `users`) are included as dependencies
- Target table (`transactions.user_order_summary`) is correctly identified as output

## Next Steps

- Read the [API Usage](../user-guide/api-usage.md) guide for detailed API options
- Read the [CLI Usage](../user-guide/cli-usage.md) for easy-to-use command-line features
- Explore [Database Integration](../user-guide/database-integration.md) for schema validation and data type retrieval
