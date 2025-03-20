import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import sqlparse
import streamlit as st

from sqldeps.database import PostgreSQLConnector

# Import the necessary components from sqldeps
from sqldeps.llm_parsers import create_extractor

st.set_page_config(
    page_title="SQL Dependency Extractor",
    page_icon="🔍",
    layout="wide",
)


def main() -> None:  # noqa: C901
    st.title("SQL Dependency Extractor")
    st.sidebar.header("Configuration")

    # Framework selection
    framework = st.sidebar.selectbox(
        "Select Framework",
        options=["groq", "openai", "deepseek"],
        index=0,
    )

    # Model selection based on framework
    model_options = {
        "groq": [
            "llama-3.3-70b-versatile",
            "gemma2-9b-it",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
        ],
        "openai": ["gpt-4o", "gpt-4o-mini"],
        "deepseek": ["deepseek-chat"],
    }

    model = st.sidebar.selectbox(
        "Select Model",
        options=model_options[framework],
        index=0,
    )

    # Custom prompt file upload
    st.sidebar.subheader("Custom Prompt (Optional)")
    prompt_file = st.sidebar.file_uploader(
        "Upload custom prompt YAML file", type=["yml", "yaml"]
    )

    # Database connection section
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
        # Password is handled through .env or ~/.pgpass
        db_target_schemas = st.sidebar.text_input(
            "Target Schemas (comma-separated)", value="public"
        )

        st.sidebar.info("Password should be set in .env as DB_PASSWORD or in ~/.pgpass")

    # SQL Input
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
                    framework=framework, model=model, prompt_path=temp_prompt_path
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
                        # Password is retrieved from .env or ~/.pgpass
                        conn = PostgreSQLConnector(
                            host=db_config["host"],
                            port=db_config["port"],
                            database=db_config["database"],
                            username=db_config["username"],
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
                        st.markdown("#### DataFrame")
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
                            # Add option to download just the validation matches
                            matches_only = db_schema_match[
                                db_schema_match["exact_match"]
                            ]
                            if not matches_only.empty:
                                validation_csv = matches_only.to_csv(index=False)
                                st.download_button(
                                    label="Download Exact Matches",
                                    data=validation_csv,
                                    file_name="exact_matches.csv",
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
