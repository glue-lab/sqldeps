# SQLDeps: SQL Dependency Extractor

<p align="center">
  <img src="https://github.com/glue-lab/sqldeps/blob/main/docs/assets/images/sqldeps_logo.png?raw=true" alt="SQLDeps Logo" width="300">
</p>

<p align="left">
<a href="https://github.com/glue-lab/sqldeps/actions/workflows/ci.yml" target="_blank">
    <img src="https://github.com/glue-lab/sqldeps/actions/workflows/ci.yml/badge.svg" alt="Test">
</a>
<a href="https://sqldeps.readthedocs.io/en/latest/" target="_blank">
    <img src="https://readthedocs.org/projects/sqldeps/badge/?version=latest" alt="Documentation">
</a>
<a href="https://pypi.org/project/sqldeps" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/sqldeps.svg?color=%2334D058" alt="Supported Python versions">
</a>
<a href="https://pypi.org/project/sqldeps" target="_blank">
    <img src="https://img.shields.io/pypi/v/sqldeps?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://opensource.org/licenses/MIT" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</a>
</p>

A tool that automatically extracts and maps SQL dependencies and outputs using Large Language Models (LLMs).

---

- **Documentation**: [https://sqldeps.readthedocs.io/](https://sqldeps.readthedocs.io/)
- **Code repositoty**: [https://github.com/glue-lab/sqldeps](https://sqldeps.readthedocs.io/)

---

## Overview

SQLDeps analyzes SQL scripts to identify:

1. **Dependencies**: Tables and columns that must exist BEFORE query execution
2. **Outputs**: Tables and columns permanently CREATED or MODIFIED by the query

It intelligently filters out temporary constructs like CTEs and derived tables, focusing only on the real database objects that matter.

### Benefits

- 🛠️ **Change Management:** Safely modify schemas by identifying true dependencies
- 💾 **Storage Optimization:** Focus resources on essential tables and columns
- 🚢 **Migration Planning:** Precisely determine what needs to be migrated
- 📝 **Project Documentation:** Create comprehensive maps of database dependencies

## Installation

```bash
pip install sqldeps
```

## Quick Start

SQLDeps provides both API and CLI interfaces:
- **API**: Enables flexibility for Python developers to integrate with their applications
- **CLI**: Offers an easy-to-use command-line interface for quick analysis

### API Usage

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

### CLI Usage

```bash
# Basic example with default settings
sqldeps path/to/query.sql

# Specify framework and output format
sqldeps path/to/query.sql --framework=openai --model=gpt-4o-mini -o query_deps.csv

# Process a folder recursively with database validation
sqldeps data/sql_folder \
    --recursive \
    --framework=deepseek \
    --db-match-schema \
    --db-target-schemas public,sales \
    --db-credentials configs/database.yml \
    -o folder_deps.csv
```

```bash
# Access CLI help
sqldeps --help
                                                                                                                                                                                         
 Usage: sqldeps [OPTIONS] COMMAND [ARGS]...                                                                                                                                              
                                                                                                                                                                                         
 SQL Dependency Extractor - Analyze SQL files to extract table and column dependencies                                                                                                   
                                                                                                                                                                                         
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version                     Show the version and exit.                                                                                                                              │
│ --install-completion          Install completion for the current shell.                                                                                                               │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                        │
│ --help                        Show this message and exit.                                                                                                                             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ extract   Extract SQL dependencies from file or folder.                                                                                                                               │
│ app       Run the SQLDeps web application                                                                                                                                             │
│ cache     Manage SQLDeps cache                                                                                                                                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

# Access CLI help for extraction
$ sqldeps extract --help
                                                                                                                                                                                         
 Usage: sqldeps extract [OPTIONS] FPATH                                                                                                                                                  
                                                                                                                                                                                         
 Extract SQL dependencies from file or folder.                                                                                                                                           
 This tool analyzes SQL files to identify table and column dependencies, optionally validating them against a real database schema.                                                      
                                                                                                                                                                                         
╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    fpath      PATH  SQL file or directory path [default: None] [required]                                                                                                           │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --framework                                      TEXT     LLM framework to use [groq, openai, deepseek] [default: groq]                                                               │
│ --model                                          TEXT     Model name for the selected framework [default: None]                                                                       │
│ --prompt                                         FILE     Path to custom prompt YAML file [default: None]                                                                             │
│ --recursive          -r                                   Recursively scan folder for SQL files                                                                                       │
│ --db-match-schema        --no-db-match-schema             Match dependencies against database schema [default: no-db-match-schema]                                                    │
│ --db-target-schemas                              TEXT     Comma-separated list of target schemas to validate against [default: public]                                                │
│ --db-credentials                                 FILE     Path to database credentials YAML file [default: None]                                                                      │
│ --db-dialect                                     TEXT     Database dialect to use for schema validation [default: postgresql]                                                         │
│ --n-workers                                      INTEGER  Number of workers for parallel processing. Use -1 for all CPU cores, 1 for sequential processing. [default: 1]              │
│ --rpm                                            INTEGER  Maximum requests per minute for API rate limiting (0 to disable) [default: 100]                                             │
│ --use-cache              --no-use-cache                   Use local cache for SQL extraction results [default: use-cache]                                                             │
│ --clear-cache            --no-clear-cache                 Clear local cache after processing [default: no-clear-cache]                                                                │
│ --output             -o                          PATH     Output file path for extracted dependencies [default: dependencies.json]                                                    │
│ --help                                                    Show this message and exit.                                                                                                 │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

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

-- Truncate an existing table before repopulating
TRUNCATE TABLE order_summary;
```

SQLDeps will extract:

```json
{
  "dependencies": {
    "orders": ["user_id"],
    "users": ["id", "status"],
    "order_summary": []
  },
  "outputs": {
    "transactions.user_order_summary": ["*"],
    "order_summary": []
  }
}
```

Note how:
- CTE (`user_orders`) is correctly excluded
- Real source tables (`orders`, `users`) are included as dependencies
- Target tables (`transactions.user_order_summary`, `order_summary`) are correctly identified as outputs
- For `TRUNCATE` operations, the table appears in both dependencies and outputs because it must exist before truncating and the operation modifies the table

## Supported Models

All models available on [Groq](https://console.groq.com/docs/models), [OpenAI](https://platform.openai.com/docs/models), and [DeepSeek](https://api-docs.deepseek.com/).  
For up-to-date pricing details, please check [Groq](https://groq.com/pricing/), [OpenAI](https://platform.openai.com/docs/pricing), [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing).

## API Keys / Configuration

You'll need to set up API keys for your chosen LLM provider. Create a `.env` file in your project root (see the provided `.env.example`):

```
# LLM API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Database credentials (for schema validation)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
DB_USER=username
DB_PASSWORD=password
```

For custom database YAML configuration file (optional): 

```yaml
# database.yml
database:
  host: localhost
  port: 5432
  database: mydatabase
  username: username
  password: password
```

## Advanced Usage

### Database Schema Validation

```python
from sqldeps.database import PostgreSQLConnector
from sqldeps.llm_parsers import create_extractor

# Extract dependencies
extractor = create_extractor(framework="openai", model="gpt-4o")
result = extractor.extract_from_file('query.sql')

# Connect to database and validate
conn = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="mydatabase",
    username="username"
)

# Match extracted dependencies against database schema
validated_schema = extractor.match_database_schema(
    result,
    db_connection=conn,
    target_schemas=["public", "sales"]
)

# View validation results (pandas DataFrame)
print(validated_schema)
```

### Processing Multiple Files

```python
# Extract dependencies from all SQL files in a folder
result = extractor.extract_from_folder('/path/to/sql_folder', recursive=True)
```

### Using Custom Prompts

You can customize the prompts used to instruct the LLM:

```python
# Create extractor with custom prompt
extractor = create_extractor(
    framework="groq",
    model="llama-3.3-70b-versatile",
    prompt_path="path/to/custom_prompt.yml"
)
```

The custom prompt YAML should include:

```yaml
system_prompt: |
  You are a SQL analyzer that extracts two key elements from SQL queries:

  1. DEPENDENCIES: Tables and columns that must exist BEFORE query execution.
  2. OUTPUTS: Tables and columns permanently CREATED or MODIFIED by the query.

  # Add detailed instructions for the LLM here...

user_prompt: |
  Extract SQL dependencies and outputs from this query:
  {sql}
```

## Web Application

SQLDeps includes a Streamlit-based web interface for interactive exploration of single SQL files:

```bash
# Install with web app dependencies
pip install "sqldeps[app]"

# Run the app
streamlit run app/main.py
```

**Note**: The web application is currently designed for single-file extraction and demonstration purposes. For processing multiple files or entire folders, use the API or CLI.

## Documentation

For comprehensive documentation, including API reference and examples, visit [https://sqldeps.readthedocs.io](https://sqldeps.readthedocs.io/).

## Contributing

Contributions are welcome! 

- Found a bug? Please open an issue with detailed information.
- Missing a feature? Feel free to suggest enhancements or submit a pull request.

Check out the [issues page](https://github.com/glue-lab/sqldeps/issues) or submit a pull request.

## License

MIT