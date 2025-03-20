# Quick Start

SQLDeps provides both API and CLI interfaces for extracting dependencies from SQL queries.

## API Usage

```python
from sqldeps.llm_parsers import create_extractor

# Create extractor with default settings (framework="groq", model="llama-3.3-70b-versatile")
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
sqldeps path/to/query.sql

# Specify framework and output format
sqldeps path/to/query.sql --framework=openai --model=gpt-4o -o query_deps.csv

# Process a folder recursively with database validation
sqldeps data/sql_folder \
    --recursive \
    --framework=deepseek \
    --db-match-schema \
    --db-target-schemas public,sales \
    --db-credentials configs/database.yml \
    -o folder_deps.csv
```

## Web Application

SQLDeps includes a Streamlit-based web interface for interactive exploration:

```bash
# Install with web app dependencies
pip install "sqldeps[app]"

# Run the app
streamlit run app/main.py
```

## Example Output

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
- Real source tables (`orders`, `users`) and respective columns are identified as dependencies
- Target table (`transactions.user_order_summary`) is identified as an output

Next steps:

- Read the [API Usage](../user-guide/api-usage.md) guide for detailed and flexible API options
- Learn about [CLI Usage](../user-guide/cli-usage.md) for command-line features
- Explore [Database Integration](../user-guide/database-integration.md) for schema validation
