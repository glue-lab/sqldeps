# LLM Parsers Reference

SQLDeps provides several LLM-based parsers for extracting SQL dependencies and a factory function to create them.

## Factory Function

The main entry point for creating extractors is the `create_extractor()` function:

```python
from sqldeps.llm_parsers import create_extractor
```

### Function Signature

```python
def create_extractor(
    framework: str = "groq",
    model: str | None = None,
    params: dict | None = None,
    prompt_path: Path | None = None,
) -> BaseSQLExtractor:
    """Create an appropriate SQL extractor based on the specified framework."""
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `framework` | `str` | `"groq"` | The LLM framework to use (`"groq"`, `"openai"`, or `"deepseek"`) |
| `model` | `str \| None` | `None` | The model name within the selected framework (uses default if `None`) |
| `params` | `dict \| None` | `None` | Additional parameters to pass to the LLM API |
| `prompt_path` | `Path \| None` | `None` | Path to a custom prompt YAML file |

### Default Models

If no model is specified, the following defaults are used:

| Framework | Default Model |
|-----------|--------------|
| `"groq"` | `"llama-3.3-70b-versatile"` |
| `"openai"` | `"gpt-4o"` |
| `"deepseek"` | `"deepseek-chat"` |

### Usage Example

```python
# Create with defaults
extractor = create_extractor()

# Create with specific framework and model
extractor = create_extractor(
    framework="openai",
    model="gpt-4o-mini"
)

# Create with custom parameters
extractor = create_extractor(
    framework="groq",
    model="llama-3.3-70b-versatile",
    params={"temperature": 0.1}
)

# Create with custom prompt
extractor = create_extractor(
    prompt_path=Path("configs/prompts/custom.yml")
)
```

## BaseSQLExtractor

All extractors inherit from the abstract `BaseSQLExtractor` class, which defines the common interface.

### Common Methods

All extractor classes provide the following methods:

#### `extract_from_query(sql: str) -> SQLProfile`

Extracts dependencies from a SQL query string.

```python
result = extractor.extract_from_query("SELECT * FROM users")
```

#### `extract_from_file(file_path: str | Path) -> SQLProfile`

Extracts dependencies from a SQL file.

```python
result = extractor.extract_from_file("path/to/query.sql")
```

#### `extract_from_folder(folder_path: str | Path, recursive: bool = False, valid_extensions: set[str] | None = None) -> SQLProfile`

Extracts and merges dependencies from all SQL files in a folder.

```python
result = extractor.extract_from_folder("path/to/sql_folder", recursive=True)
```

#### `match_database_schema(dependencies: SQLProfile, db_connection: SQLBaseConnector, target_schemas: list[str] | None = None) -> pd.DataFrame`

Matches extracted dependencies against actual database schema.

```python
validated_schema = extractor.match_database_schema(
    dependencies,
    db_connection=conn,
    target_schemas=["public", "sales"]
)
```

## Specific Extractor Classes

SQLDeps provides three extractor implementations:

### GroqExtractor

```python
from sqldeps.llm_parsers import GroqExtractor

extractor = GroqExtractor(
    model="llama-3.3-70b-versatile",
    params={"temperature": 0},
    api_key="your-groq-api-key",  # Optional, can use GROQ_API_KEY env var
    prompt_path=None  # Optional
)
```

### OpenaiExtractor

```python
from sqldeps.llm_parsers import OpenaiExtractor

extractor = OpenaiExtractor(
    model="gpt-4o",
    params={"temperature": 0},
    api_key="your-openai-api-key",  # Optional, can use OPENAI_API_KEY env var
    prompt_path=None  # Optional
)
```

### DeepseekExtractor

```python
from sqldeps.llm_parsers import DeepseekExtractor

extractor = DeepseekExtractor(
    model="deepseek-chat",
    params={"temperature": 0},
    api_key="your-deepseek-api-key",  # Optional, can use DEEPSEEK_API_KEY env var
    prompt_path=None  # Optional
)
```

## Customizing Prompts

Each extractor uses a prompt template to instruct the LLM. You can customize the prompt by creating a YAML file:

```yaml
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

The prompt must include both `system_prompt` and `user_prompt` sections. The `{sql}` placeholder in the `user_prompt` will be replaced with the actual SQL query.
