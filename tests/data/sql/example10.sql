-- PostgreSQL function that uses CTEs and creates a table
CREATE OR REPLACE FUNCTION generate_sales_report()
RETURNS void AS $$
BEGIN
    -- Use CTEs to process data
    WITH cte_sales AS (
        SELECT 
            s.id AS sale_id, 
            s.amount, 
            c.customer_name 
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
    ),
    cte_products AS (
        SELECT 
            p.product_id, 
            p.product_name 
        FROM products p
    )
    -- Insert the processed data into a new table
    INSERT INTO reports.sales_report (sale_id, customer_name, product_name)
    SELECT 
        cte_sales.sale_id, 
        cte_sales.customer_name, 
        cte_products.product_name
    FROM cte_sales
    JOIN cte_products ON cte_sales.sale_id = cte_products.product_id;
END;
$$ LANGUAGE plpgsql;

-- Truncate a table
TRUNCATE TABLE logs;

-- Query from a specific database
SELECT 
    my_db.orders.order_id, 
    my_db.orders.order_date, 
    my_db.orders.total_amount 
FROM my_db.orders;

-- Select all columns from a table
SELECT * 
FROM employees
LIMIT 10;
