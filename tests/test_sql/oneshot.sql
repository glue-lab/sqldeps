-- Dependencies and Outcomes should include all source tables/columns even when inside a function
CREATE OR REPLACE FUNCTION generic_function()
RETURNS void AS $$
BEGIN
    -- CTE (Common Table Expression) - temporary result set
    -- CTEs themselves should NOT be extracted as dependencies or outcomes
    -- but their source tables and columns ARE dependencies
    WITH temp_cte AS (
        SELECT 
            a.col1 AS alias1,  -- column alias (exclude from dependencies)
            a.col2,
            b.col3,
            COUNT(c.col1) AS count_result  -- aggregation result (exclude from dependencies)
        FROM source_table_a a  -- table alias, should resolve to "source_table_a" in dependencies
        JOIN source_table_b b ON a.col4 = b.col1  -- join columns are dependencies
        LEFT JOIN source_table_c c ON b.col1 = c.col2
        WHERE a.col5 > 100  -- WHERE columns are dependencies
          AND b.col6 = 'ACTIVE'
          -- Subquery in WHERE clause - these tables/columns are dependencies
          AND c.col3 IN (SELECT col1 FROM source_table_d WHERE col2 = 'special')
        GROUP BY a.col1, a.col2, b.col3  -- GROUP BY columns are dependencies
    )
    -- INSERT operation - target table is a dependency
    -- Column names in target are dependencies
    INSERT INTO schema1.target_table (target_col1, target_col2, target_col3)
    SELECT 
        alias1,
        col3,
        -- CASE expression - all examined columns are dependencies
        CASE 
            WHEN col2 > 1000 THEN 'High'
            WHEN col2 > 500 THEN 'Medium'
            ELSE 'Low'
        END
    FROM temp_cte  -- CTE reference (not a real table dependency)
    WHERE count_result > 10;  -- Reference to computed column (not a dependency)

    -- UPDATE operation - both target and source tables/columns are dependencies
    -- Aliases should be resolved to real table names
    UPDATE target_table_e e
    SET status_col = 'Updated',
        date_col = CURRENT_DATE,  -- Function with no column dependencies
        amount_col = sq.total_val  -- Referencing derived column from subquery
    FROM (
        -- Subquery creating a derived table - not a dependency itself
        -- but its source tables/columns ARE dependencies
        SELECT f.id_col, SUM(g.amount_col) AS total_val
        FROM source_table_f f
        JOIN source_table_g g ON f.id_col = g.parent_id_col
        WHERE g.status_col = 'Active'
        GROUP BY f.id_col
    ) sq  -- Subquery alias (not a dependency)
    WHERE e.id_col = sq.id_col
    -- Nested subquery in WHERE - these tables/columns are dependencies
    AND e.category_col IN (
        SELECT category_col FROM schema2.lookup_table WHERE active_col = true
    );
END;
$$ LANGUAGE plpgsql;

-- DDL operation - table is a dependency but no columns needed
-- Empty column list for this table is expected
TRUNCATE TABLE schema3.log_table;

-- Query with window functions, schema qualification, and complex conditions
SELECT 
    schema4.user_table.id_col,
    schema4.user_table.name_col,
    schema4.user_table.email_col,
    -- Window function - partition/order columns are dependencies
    -- but the result is not a dependency
    ROW_NUMBER() OVER (PARTITION BY schema4.user_table.dept_col ORDER BY schema4.user_table.date_col) as rank_val,
    -- Correlated subquery - creates additional table/column dependencies
    (SELECT COUNT(*) FROM schema4.order_table WHERE user_id_col = schema4.user_table.id_col) as count_val
FROM schema4.user_table
WHERE schema4.user_table.status_col = 'Active'
-- Subquery in WHERE creating more dependencies
AND schema4.user_table.dept_col IN (
    SELECT id_col FROM schema4.dept_table WHERE region_col = 'North'
)
LIMIT 100;  -- LIMIT doesn't affect dependencies

-- SELECT * example - when a table uses "SELECT *", its column dependency 
-- should be represented as ["*"] regardless of other column references
SELECT * 
FROM schema5.country_table
WHERE iso_code_col = 'US' AND active_col = true;