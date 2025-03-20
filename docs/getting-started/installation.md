# Installation

## Prerequisites

- Python 3.10 or higher
- API keys for your preferred LLM provider (OpenAI, Groq, or DeepSeek)

## Install from PyPI

The simplest way to install SQLDeps is via pip:

```bash
pip install sqldeps
```

For additional functionality, you can install optional dependencies:

```bash
# Install with web app dependencies
pip install "sqldeps[app]"

# Install with data visualization dependencies
pip install "sqldeps[dataviz]"

# Install all optional dependencies
pip install "sqldeps[app,dataviz]"
```

## Setup API Keys

SQLDeps requires API keys for the LLM providers you want to use. 

### Option 1: Environment Variables

Create a `.env` file in your project root with your API keys:

```
# LLM API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional: Database credentials (for schema validation)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
DB_USER=username
DB_PASSWORD=password
```

### Option 2: Direct Configuration

You can also provide API keys directly when creating an extractor:

```python
from sqldeps.llm_parsers import create_extractor

extractor = create_extractor(
    framework="openai",
    model="gpt-4o-mini",
    api_key="your-api-key-here"
)
```

## Database Configuration (Optional)

If you plan to use the database schema validation features, you can set up your database credentials in several ways:

### YAML Configuration File

```yaml
# database.yml
database:
  host: localhost
  port: 5432
  database: mydatabase
  username: username
  password: password
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

SQLDeps also supports reading credentials from the standard PostgreSQL password file (`~/.pgpass`).

## Verify Installation

You can verify your installation by running:

```bash
sqldeps --help
```

This should display the command-line help information for SQLDeps.
