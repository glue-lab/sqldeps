# Installation

## Prerequisites

- Python 3.10 or higher
- API keys for your preferred LLM provider (Groq, OpenAI, or DeepSeek)

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
pip install "sqldeps[app,database,dataviz]"
```

## Setup API Keys

SQLDeps requires API keys for the LLM providers you want to use. These keys are set through environment variables.

### Environment Variables

Create a `.env` file in your project root with your API keys:

```
# LLM API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Database credentials (for schema validation)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydatabase
DB_USER=username
DB_PASSWORD=password
```

SQLDeps will automatically load variables from the .env file when you import the package.

> **Tip:** [Groq](https://console.groq.com/keys) offers free tokens without requiring payment details, making it ideal for getting started quickly.

## Database Configuration (Optional)

If you plan to use the database features, you can set up your database credentials in several ways:

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
