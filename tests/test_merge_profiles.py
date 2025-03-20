from sqldeps.models import SQLProfile
from sqldeps.utils import merge_profiles


def test_merge_sql_analyses() -> None:
    """
    Test merging multiple SQLProfile objects with different schemas, tables,
    and cases where '*' (wildcard) appears in column dependencies.

    Ensures:
    1. Unique tables are merged correctly.
    2. Columns are merged per table unless '*' is present.
    3. When '*' appears in a table's columns, it takes precedence,
    and other columns are ignored.
    4. Both dependencies and outputs are properly merged.
    """
    # First analysis: Normal tables with specific columns
    analysis1 = SQLProfile(
        dependencies={
            "public.users": ["id", "name"],  # Specific columns for 'users'
            "sales.orders": ["order_id", "user_id"],  # Specific columns for 'orders'
        },
        outputs={
            "report.monthly_sales": ["month", "total_sales"],
        },
    )

    # Second analysis: A mix of specific columns and a wildcard '*'
    analysis2 = SQLProfile(
        dependencies={
            "sales.orders": [
                "*"
            ],  # Wildcard '*' should override specific columns from analysis1
            "products": ["product_id", "name"],  # Specific columns for 'products'
        },
        outputs={
            "report.monthly_sales": ["category"],  # Adding a column to existing outcome
            "temp.product_summary": ["product_id", "sales_count"],  # New outcome table
        },
    )

    # Third analysis: Another table and more columns for 'users'
    analysis3 = SQLProfile(
        dependencies={
            "public.users": ["email"],  # Adding 'email' to 'users' table
            "payments": ["payment_id", "user_id"],  # Specific columns for 'payments'
        },
        outputs={
            "report.user_activity": ["user_id", "last_login"],  # New outcome table
            "temp.product_summary": ["*"],  # Wildcard should override specific columns
        },
    )

    # Merge all analyses together
    merged_analysis = merge_profiles([analysis1, analysis2, analysis3])

    # Expected merged result: Distinct tables and merged columns
    # for both dependencies and outputs
    expected_result = SQLProfile(
        dependencies={
            "payments": [
                "payment_id",
                "user_id",
            ],  # Payments should contain both columns
            "products": ["name", "product_id"],  # Products should remain unchanged
            "public.users": [
                "email",
                "id",
                "name",
            ],  # Users should include all unique columns
            "sales.orders": [
                "*"
            ],  # '*' takes precedence and should be the only column here
        },
        outputs={
            "report.monthly_sales": [
                "category",
                "month",
                "total_sales",
            ],  # Combined columns from analysis1 and analysis2
            "report.user_activity": ["last_login", "user_id"],  # From analysis3
            "temp.product_summary": ["*"],  # '*' takes precedence from analysis3
        },
    )

    # Validate that the merged analysis matches the expected result
    assert merged_analysis.to_dict() == expected_result.to_dict(), (
        "Merged SQL analyses do not match expected output"
    )
