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
<!-- - **Simulate SQLDeps savings for your team**: [Streamlit WebApp](https://sqldeps-simulator.streamlit.app/) -->


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

For additional functionality:

```bash
# Install with web app dependencies
pip install "sqldeps[app]"

# Install with data visualization dependencies
pip install "sqldeps[dataviz]"

# Install all optional dependencies
pip install "sqldeps[app,dataviz]"
```

## Quick Start

SQLDeps provides both API and CLI interfaces:
- **API**: Flexible for Python developers to integrate into scripts, notebooks, or applications.
- **CLI**: Fast and user-friendly for analyzing files or folders directly from the command line.

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
sqldeps extract path/to/query.sql

# Specify framework and output format
sqldeps extract path/to/query.sql --framework=openai --model=gpt-4o -o results.json

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

### Web Application

SQLDeps also includes a Streamlit-based web interface:

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

## Supported Models

All models available on [Groq](https://console.groq.com/docs/models), [OpenAI](https://platform.openai.com/docs/models), and [DeepSeek](https://api-docs.deepseek.com/).  
For up-to-date pricing details, please check [Groq](https://groq.com/pricing/), [OpenAI](https://platform.openai.com/docs/pricing), [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing).

## API Keys / Configuration

You'll need to set up API keys for your chosen LLM provider. Create a `.env` file in your project root:

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

> **Tip:** [Groq](https://console.groq.com/keys) offers free tokens without requiring payment details, making it ideal for getting started quickly.

## Advanced Usage

### Database Schema Matching

SQLDeps allows the user to match SQLDeps results (table/column dependencies and outputs) with database schemas to retrieve column data types.

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
matching_schema = extractor.match_database_schema(
    result,
    db_connection=conn,
    target_schemas=["public", "sales"]
)

# View validation results as a pandas DataFrame
print(matching_schema)
```

For custom database YAML configuration file (optional):

```yml
# database.yml
database:
  host: localhost
  port: 5432
  database: mydatabase
  username: username
  password: password
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

### Interactive Visualization of SQL Dependency Graphs

SQLDeps provides built-in visualization capabilities to help you understand complex SQL dependencies:

```python
from sqldeps.llm_parsers import create_extractor
from sqldeps.visualization import visualize_sql_dependencies

# Create an interactive network graph from multiple SQL files
extractor = create_extractor()
sql_profiles = extractor.extract_from_folder("path/to/folder", recursive=False)

# Generate an interactive visualization (saving output to an HTML file)
figure = visualize_sql_dependencies(sql_profiles, output_path="dependencies.html")

# Show figure
figure.show()
```

## Documentation

For comprehensive documentation, including API reference and examples, visit [https://sqldeps.readthedocs.io](https://sqldeps.readthedocs.io/).

## Contributing

Contributions are welcome! 

- Found a bug? Please [open an issue](https://github.com/glue-lab/sqldeps/issues) with detailed information.
- Missing a feature? Feel free to [suggest enhancements](https://github.com/glue-lab/sqldeps/discussions/categories/ideas) or submit a pull request.

Please check out the [Contributing Guide](https://sqldeps.readthedocs.io/en/latest/contributing/) for details.


## License

MIT
