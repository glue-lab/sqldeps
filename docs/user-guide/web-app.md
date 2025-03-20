# Web Application

SQLDeps includes a Streamlit-based web interface for interactive SQL dependency exploration.

## Installation

To use the web application, install SQLDeps with the app dependencies:

```bash
pip install "sqldeps[app]"
```

## Starting the App

Start the web application with:

```bash
streamlit run app/main.py
```

This will launch the Streamlit app in your default web browser, typically at `http://localhost:8501`.

## Using the Web Interface

The web interface provides an intuitive way to analyze SQL dependencies:

### Configuration Panel

On the left sidebar, you'll find configuration options:

1. **Framework Selection**: Choose between Groq, OpenAI, or DeepSeek
2. **Model Selection**: Select the specific model to use
3. **Custom Prompt**: Optionally upload a custom prompt YAML file
4. **Database Connection**: Configure database connection for schema validation
5. **SQL Input**: Upload a SQL file or enter SQL directly

### Analysis Results

After clicking "Extract Dependencies", the main panel displays:

1. **SQL Query**: The formatted SQL query that was analyzed
2. **Extracted Dependencies**:
    - Tables listed in a clear format
    - Columns organized by table
    - Database schema validation results (if enabled)
    - DataFrame representation
    - Raw JSON output

### Download Options

The app provides options to download the results as:

- CSV file
- JSON file
- Data types for dependencies matching database (when enabled)

## Database Matching

To enable database schema matching:

1. Check the "Enable Database Schema Validation" option
2. Enter database connection details:
    - Host
    - Port
    - Database name
    - Username
    - Target schemas (comma-separated)

When database matching is enabled, the app will:

1. Connect to the specified database
2. Retrieve schema information for the target schemas
3. Match extracted dependencies against the actual schema
4. Display dependency data types showing exact matches and schema-agnostic dependencies

## Example Workflow

1. Select your preferred framework and model
2. Either upload a SQL file or enter a SQL query
3. Optionally configure database schema validation
4. Click "Extract Dependencies" to analyze
5. Explore the results in the main panel
6. Download the results in your preferred format

## Notes

The web application is designed for demonstration and exploration of single SQL files. For processing multiple files or entire folders, use the CLI or API interfaces.

## Customization

The web application can be customized by modifying the `app/main.py` file:

- Adjust default connection parameters
- Change the list of available models
- Add custom validation features
- Modify the UI layout
- Etc
