# API Usage

SQLDeps provides a comprehensive Python API for extracting SQL dependencies and validating them against database schemas.

## Creating an Extractor

The main entry point for using SQLDeps is the `create_extractor()` function:

```python
from sqldeps.llm_parsers import create_extractor

# Create extractor with default settings (framework="groq", model="llama-3.3-70b-versatile")
extractor = create_extractor()

# Specify a different framework and model
extractor = create_extractor(
    framework="openai",
    model="gpt-4o"
)

# Specify additional parameters for the LLM
extractor = create_extractor(
    framework="groq",
    model="llama-3.3-70b-versatile",
    params={"temperature": 0.1}
)

# Use a custom prompt template
extractor = create_extractor(
    framework="deepseek",
    model="deepseek-chat",
    prompt_path="path/to/custom_prompt.yml"
)
```

## Extracting Dependencies

Once you have an extractor, you can use it to extract dependencies from SQL queries, files, or folders:

### From a Query String

```python
# Extract from a SQL query string
sql_query = """
SELECT u.id, u.name, o.order_id, o.amount
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
"""

result = extractor.extract_from_query(sql_query)
```

### From a File

```python
# Extract from a SQL file
result = extractor.extract_from_file("path/to/query.sql")
```

### From a Folder

```python
# Extract from all SQL files in a folder
result = extractor.extract_from_folder("path/to/sql_folder")

# Extract recursively from all SQL files in a folder and subfolders
result = extractor.extract_from_folder("path/to/sql_folder", recursive=True)

# Extract from files with specific extensions
result = extractor.extract_from_folder(
    "path/to/sql_folder",
    recursive=True,
    valid_extensions={"sql", "pgsql", "tsql"}
)
```

## Working with Results

The `extract_*` methods return a `SQLProfile` object that contains the extracted dependencies and outputs:

```python
# Access dependencies and outputs as dictionaries
dependencies = result.dependencies  # Dict of tables and their columns
outputs = result.outputs  # Dict of tables and columns created or modified

# Get a list of all referenced tables
tables = result.dependency_tables

# Get a list of all output tables
output_tables = result.outcome_tables

# Convert to a dictionary
result_dict = result.to_dict()

# Convert to a DataFrame for easier analysis
result_df = result.to_dataframe()
```

## Database Schema Validation

You can validate the extracted dependencies against a real database schema:

```python
from sqldeps.database import PostgreSQLConnector

# Connect to the database
db_conn = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="mydatabase",
    username="user"
    # Password from .pgpass or environment variables
)

# Match extracted dependencies against database schema
validated_schema = extractor.match_database_schema(
    result,  # The SQLProfile from extraction
    db_connection=db_conn,
    target_schemas=["public", "sales"]  # Optional: schemas to validate against
)

# The result is a DataFrame with database schema information
print(validated_schema)

# Filter for exact matches
exact_matches = validated_schema[validated_schema["exact_match"]]

# Filter for schema-agnostic matches or cross-schema matches
missing_deps = validated_schema[~validated_schema["exact_match"]]
```

## Custom Prompts

You can create custom prompts to guide the LLM extraction process:

```yaml
# custom_prompt.yml
system_prompt: |
  You are a SQL analyzer that extracts two key elements from SQL queries:
  
  1. DEPENDENCIES: Tables and columns that must exist BEFORE query execution.
  2. OUTPUTS: Tables and columns permanently CREATED or MODIFIED by the query.
  
  # Add detailed instructions for the LLM here...

user_prompt: |
  Extract SQL dependencies (tables/columns needed BEFORE execution) and outputs 
  (tables/columns CREATED or MODIFIED) from this query.
  
  Respond ONLY with JSON in this exact format:
  {{
    "dependencies": {{"table_name": ["column1", "column2"]}},
    "outputs": {{"table_name": ["column1", "column2"]}}
  }}
  
  SQL query to analyze:
  {sql}
```

Use the custom prompt with:

```python
extractor = create_extractor(prompt_path="path/to/custom_prompt.yml")
```
