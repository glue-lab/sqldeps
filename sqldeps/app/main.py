"""Web application for interactive SQLDeps analysis.

This module provides a Streamlit-based web interface for extracting
and visualizing SQL dependencies.
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import sqlparse
import streamlit as st
from sqlalchemy import text

from sqldeps.database import PostgreSQLConnector
from sqldeps.llm_parsers import create_extractor

# Logo paths
ASSETS_DIR = Path(__file__).parent / "assets" / "images"
LOGO_GRAY_PATH = ASSETS_DIR / "sqldeps_gray.png"
LOGO_WHITE_PATH = ASSETS_DIR / "sqldeps_white.png"

# App configuration
st.set_page_config(
    page_title="SQL Dependency Extractor",
    page_icon=str(LOGO_WHITE_PATH),
    layout="wide",
)


def main() -> None:  # noqa: C901
    """Main function for the SQLDeps web application.

    This function:
    1. Sets up the Streamlit interface with sidebar options
    2. Handles file uploads or direct SQL input
    3. Processes SQL to extract dependencies
    4. Optionally validates against a database
    5. Displays results in an organized, interactive format

    Returns:
        None
    """
    st.title("SQL Dependency Extractor")
    st.sidebar.image(str(LOGO_GRAY_PATH))
    st.sidebar.header("Configuration")

    # Framework selection
    framework = st.sidebar.selectbox(
        "Select Framework",
        options=["groq", "openai", "deepseek"],
        index=1,
    )

    # Model selection based on framework
    model_options = {
        "groq": [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "gemma2-9b-it",
            "mistral-saba-24b",
            "qwen-qwq-32b",
        ],
        "openai": ["gpt-4.1-mini", "gpt-4.1", "gpt-4o", "o3-mini", "o4-mini"],
        "deepseek": ["deepseek-chat"],
    }

    model = st.sidebar.selectbox(
        "Select Model",
        options=model_options[framework],
        index=0,
    )

    # API Key input section
    # st.sidebar.subheader("API Key (Optional)")
    api_key_mapping = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    api_key_env_var = api_key_mapping.get(framework, "")
    if api_key_env_var:
        placeholder = "gsk-..." if framework == "groq" else "sk-..."
        api_key = st.sidebar.text_input(
            f"{api_key_env_var}", type="password", placeholder=placeholder
        )
        if api_key:
            os.environ[api_key_env_var] = api_key

            # Add test API connection button
            if st.sidebar.button("Test API Connection"):
                with st.sidebar.status("Testing API connection..."):
                    try:
                        # Create a minimal extractor to test API key validity
                        test_extractor = create_extractor(model=f"{framework}/{model}")
                        # Simple test query
                        test_extractor.extract_from_query("SELECT 1")
                        st.sidebar.success("✅ API connection successful!")
                    except Exception as e:
                        st.sidebar.error(f"❌ API connection failed: {e!s}")
            else:
                st.sidebar.success(f"✅ {api_key_env_var} set")

        st.sidebar.info(
            "API key will be used for this session only. "
            "If not provided, the app will look for the key in environment variables."
        )

    # Custom prompt file upload
    st.sidebar.markdown("---")
    st.sidebar.subheader("Custom Prompt (Optional)")
    prompt_file = st.sidebar.file_uploader(
        "Upload custom prompt YAML file", type=["yml", "yaml"]
    )

    # Database connection section
    st.sidebar.markdown("---")
    st.sidebar.subheader("Database Connection (Optional)")
    enable_db = st.sidebar.checkbox("Enable Database Schema Validation")

    db_config = {}
    if enable_db:
        db_config["host"] = st.sidebar.text_input("Host")
        db_config["port"] = st.sidebar.number_input(
            "Port", value=5432, min_value=1, max_value=65535
        )
        db_config["database"] = st.sidebar.text_input("Database Name")
        db_config["username"] = st.sidebar.text_input("Username")
        db_config["password"] = st.sidebar.text_input(
            "Password (Optional)", type="password"
        )
        # Password is handled through .env or ~/.pgpass
        db_target_schemas = st.sidebar.text_input(
            "Target Schemas (comma-separated)", value="public"
        )

        # Add database test connection button
        if (
            db_config.get("host")
            and db_config.get("database")
            and db_config.get("username")
        ) and st.sidebar.button("Test Database Connection"):
            with st.sidebar.status("Testing database connection..."):
                try:
                    # Test database connection
                    conn = PostgreSQLConnector(
                        host=db_config["host"],
                        port=db_config["port"],
                        database=db_config["database"],
                        username=db_config["username"],
                        password=db_config.get("password")
                        if db_config.get("password")
                        else None,
                    )
                    # Just check if engine is available by executing a simple query
                    with conn.engine.connect() as connection:
                        connection.execute(text("SELECT 1"))
                    st.sidebar.success("✅ Database connection successful!")
                except Exception as e:
                    st.sidebar.error(f"❌ Database connection failed: {e!s}")

        st.sidebar.info(
            "If password is not provided, it will be looked up in "
            ".env as DB_PASSWORD or in ~/.pgpass"
        )

    # SQL Input
    st.sidebar.markdown("---")
    st.sidebar.subheader("SQL Input")
    input_method = st.sidebar.radio(
        "Choose input method",
        options=["Upload SQL File", "Enter SQL Query"],
    )

    sql_query = ""
    uploaded_file = None

    if input_method == "Upload SQL File":
        uploaded_file = st.sidebar.file_uploader("Upload SQL file", type=["sql"])
        if uploaded_file is not None:
            sql_query = uploaded_file.getvalue().decode("utf-8")
    else:
        sql_query = st.sidebar.text_area(
            "Enter SQL Query",
            height=300,
            placeholder="SELECT * FROM table WHERE condition...",
        )

    # Execute button
    process_button = st.sidebar.button("Extract Dependencies", type="primary")

    # Create two columns for the main content
    col1, col2 = st.columns(2)

    if process_button and (uploaded_file or sql_query):
        try:
            with st.spinner("Extracting dependencies..."):
                # Format SQL for display
                formatted_sql = sqlparse.format(
                    sql_query, reindent=True, keyword_case="upper"
                )

                # Initialize extractor
                temp_prompt_path = None
                if prompt_file:
                    # Create a temporary file to save the uploaded prompt
                    with tempfile.NamedTemporaryFile(
                        suffix=".yml", delete=False
                    ) as temp_file:
                        temp_file.write(prompt_file.getvalue())
                        temp_prompt_path = Path(temp_file.name)

                extractor = create_extractor(
                    model=f"{framework}/{model}", prompt_path=temp_prompt_path
                )

                # Extract dependencies
                if uploaded_file:
                    # Create a temporary SQL file
                    with tempfile.NamedTemporaryFile(
                        suffix=".sql", delete=False
                    ) as temp_sql_file:
                        temp_sql_file.write(uploaded_file.getvalue())
                        sql_file_path = Path(temp_sql_file.name)

                    dependencies = extractor.extract_from_file(sql_file_path)
                    # Clean up temporary file
                    os.unlink(sql_file_path)
                else:
                    dependencies = extractor.extract_from_query(sql_query)

                # Database validation if enabled
                db_schema_match = None
                if (
                    enable_db
                    and db_config.get("host")
                    and db_config.get("database")
                    and db_config.get("username")
                ):
                    try:
                        # Use provided password or fall back to .env or ~/.pgpass
                        conn = PostgreSQLConnector(
                            host=db_config["host"],
                            port=db_config["port"],
                            database=db_config["database"],
                            username=db_config["username"],
                            password=db_config.get("password")
                            if db_config.get("password")
                            else None,
                        )
                        target_schemas = [
                            schema.strip() for schema in db_target_schemas.split(",")
                        ]
                        db_schema_match = extractor.match_database_schema(
                            dependencies,
                            db_connection=conn,
                            target_schemas=target_schemas,
                        )
                        st.sidebar.success("Database connection successful")
                    except Exception as e:
                        st.sidebar.error(f"Database connection failed: {e!s}")

                # Clean up temporary prompt file if it exists
                if temp_prompt_path:
                    os.unlink(temp_prompt_path)

                # Display formatted SQL in left column
                with col1:
                    st.subheader("SQL Query")
                    st.code(formatted_sql, language="sql")

                # Display results in right column
                with col2:
                    st.subheader("Extracted Dependencies")

                    # Show tables using a more structured approach
                    st.markdown("#### Tables")
                    if dependencies.dependency_tables:
                        table_df = pd.DataFrame(
                            {"Table Name": dependencies.dependency_tables}
                        )
                        st.dataframe(
                            table_df, use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("No tables found")

                    # Show columns using expanders for each table
                    st.markdown("#### Columns by Table")
                    if dependencies.dependencies:
                        for table_name, columns in dependencies.dependencies.items():
                            with st.expander(f"Table: {table_name}"):
                                if columns:
                                    if "*" in columns:
                                        st.write("All columns (*)")
                                    else:
                                        columns_df = pd.DataFrame(
                                            {"Column Name": columns}
                                        )
                                        st.dataframe(
                                            columns_df,
                                            use_container_width=True,
                                            hide_index=True,
                                        )
                                else:
                                    st.write("No specific columns identified")
                    else:
                        st.info("No columns found")

                    # Show database validation results if available
                    if db_schema_match is not None:
                        st.markdown("#### Database Schema Validation")
                        matching_tabs = st.tabs(
                            ["All Results", "Exact Matches", "Schema-Agnostic Matches"]
                        )

                        with matching_tabs[0]:
                            st.dataframe(db_schema_match, use_container_width=True)

                        with matching_tabs[1]:
                            matches = db_schema_match[db_schema_match["exact_match"]]
                            if not matches.empty:
                                st.dataframe(matches, use_container_width=True)
                            else:
                                st.info("No exact matches found")

                        with matching_tabs[2]:
                            missing = db_schema_match[~db_schema_match["exact_match"]]
                            if not missing.empty:
                                st.dataframe(missing, use_container_width=True)
                            else:
                                st.success("All dependencies found in database schema!")

                    # Display as dataframe
                    if dependencies.to_dict()["dependencies"]:
                        st.markdown("#### DataFrame View")
                        df = dependencies.to_dataframe()
                        st.dataframe(df, use_container_width=True)

                    # Display raw JSON
                    st.markdown("#### Raw JSON")
                    st.json(dependencies.to_dict())

                    # Download buttons with additional option for DB validation
                    download_cols = (
                        st.columns(3) if db_schema_match is not None else st.columns(2)
                    )

                    with download_cols[0]:
                        # If we have database validation results, include data_type
                        if db_schema_match is not None:
                            # Use the validated schema that includes data types
                            csv = db_schema_match.to_csv(index=False)
                            filename = "dependencies_with_types.csv"
                        else:
                            # Use the simple extraction without data types
                            csv = dependencies.to_dataframe().to_csv(index=False)
                            filename = "dependencies.csv"

                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=filename,
                            mime="text/csv",
                        )

                    with download_cols[1]:
                        json_data = json.dumps(dependencies.to_dict(), indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name="dependencies.json",
                            mime="application/json",
                        )

                    if db_schema_match is not None and len(download_cols) > 2:
                        with download_cols[2]:
                            db_csv = db_schema_match.to_csv(index=False)
                            st.download_button(
                                label="Download CSV with DB-schema-matching",
                                data=db_csv,
                                file_name="db_dependencies.csv",
                                mime="text/csv",
                            )

        except Exception as e:
            st.error(f"Error extracting dependencies: {e!s}")
            st.exception(e)

    # Display instructions if no query is provided
    if not process_button or (not uploaded_file and not sql_query):
        with col1:
            st.info(
                "Enter a SQL query or upload a SQL file and click "
                "'Extract Dependencies' to analyze."
            )

            st.markdown("""
            ### Instructions
            1. Select your preferred LLM framework and model
            2. Optionally upload a custom prompt YAML file
            3. Either upload a SQL file or enter a SQL query
            4. Click 'Extract Dependencies' to analyze
            """)

        with col2:
            st.info("Dependency results will appear here.")

            st.markdown("""
            ### About
            This app extracts table and column dependencies from SQL queries using:
            - Various LLM frameworks (Groq, OpenAI, DeepSeek)
            - Custom prompts (optional)
            - Database schema validation (optional)
            - Formatted display of dependencies

            The results include:
            - List of referenced tables
            - Columns used from each table
            - DataFrame representation
            - Database validation (when enabled)
            - Downloadable CSV and JSON formats
            """)


if __name__ == "__main__":
    main()
