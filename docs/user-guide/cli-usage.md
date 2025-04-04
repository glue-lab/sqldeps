# CLI Usage

SQLDeps includes a powerful command-line interface for extracting SQL dependencies.

## Basic Usage

The basic command syntax is:

```bash
sqldeps extract PATH [OPTIONS]
```

Where `PATH` is the path to a SQL file or directory containing SQL files.

## Common Options

| Option | Description |
|--------|-------------|
| `--framework` | LLM framework to use (groq, openai, deepseek) |
| `--model` | Model name within the selected framework |
| `--prompt` | Path to custom prompt YAML file |
| `-r, --recursive` | Recursively scan folder for SQL files |
| `-o, --output` | Output file path (.json or .csv) |
| `--n-workers` | Number of workers for parallel processing (-1 for all CPUs) |
| `--rpm` | Maximum requests per minute for API rate limiting |
| `--use-cache` | Use local cache for SQL extraction results |
| `--clear-cache` | Clear local cache after processing |

## Basic Examples

```bash
# Basic usage with default settings (groq/llama-3.3-70b-versatile)
sqldeps extract path/to/query.sql

# Specify a different framework and model
sqldeps extract path/to/query.sql --framework=openai --model=gpt-4o

# Process all SQL files in a directory
sqldeps extract path/to/sql_folder

# Process recursively with a specific output file
sqldeps extract path/to/sql_folder --recursive -o results.csv

# Use a custom prompt
sqldeps extract path/to/query.sql --prompt=path/to/custom_prompt.yml

# Use parallel processing with rate limiting
sqldeps extract path/to/sql_folder --recursive --n-workers=-1 --rpm=50
```

## Database Validation

SQLDeps can validate extracted dependencies against a real database schema:

```bash
# Validate against a database
sqldeps extract path/to/query.sql \
    --db-match-schema \
    --db-target-schemas public,sales \
    --db-credentials path/to/database.yml
```

Database validation options:

| Option | Description |
|--------|-------------|
| `--db-match-schema` | Enable database schema validation |
| `--db-target-schemas` | Comma-separated list of target schemas |
| `--db-credentials` | Path to database credentials YAML file |
| `--db-dialect` | Database dialect (default: postgresql) |

## Output Formats

SQLDeps supports both JSON and CSV output formats:

```bash
# Output as JSON (default)
sqldeps extract path/to/query.sql -o results.json

# Output as CSV
sqldeps extract path/to/query.sql -o results.csv
```

## Managing Cache

SQLDeps provides commands to manage the extraction cache:

```bash
# Clear the cache
sqldeps cache clear
```

## Running the Web App

SQLDeps includes a Streamlit-based web application:

```bash
# Start the web app
sqldeps app
```

## Advanced Examples

```bash
# Complete example with all options
sqldeps extract data/sql_folder \
    --recursive \
    --framework=deepseek \
    --model=deepseek-chat \
    --prompt=configs/prompts/custom.yml \
    --db-match-schema \
    --db-target-schemas public,sales,reporting \
    --db-credentials configs/database.yml \
    --n-workers=10 \
    --rpm=100 \
    --use-cache \
    -o folder_deps.csv
```

## Help Command

For a complete list of options, use the help command:

```bash
sqldeps --help

# View help for a specific command
sqldeps extract --help
```

## Exit Codes

The CLI will return the following exit codes:

- `0`: Success
- `1`: Error (file not found, connection error, extraction failed, etc.)

## Integration with Shell Scripts

SQLDeps can be easily integrated into shell scripts:

```bash
#!/bin/bash

# Process all SQL files in a directory
sqldeps extract sql_files/ --recursive -o results.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "Dependencies extracted successfully."
else
    echo "Failed to extract dependencies."
    exit 1
fi

# Process results
cat results.json | jq '.dependencies'
```