-- This oneshot example demonstrates key SQL dependency extraction scenarios
-- including table dependencies, outputs, temporary artifacts, truncates, and more

-- Scenario 1: Simple SELECT with JOIN and WHERE clauses
SELECT 
    u.user_id, 
    u.username, 
    o.order_date,
    o.total_amount,
    p.product_name
FROM 
    schema1.users u
JOIN 
    schema1.orders o ON u.user_id = o.user_id
JOIN 
    schema1.order_items oi ON o.order_id = oi.order_id
JOIN 
    schema1.products p ON oi.product_id = p.product_id
WHERE 
    o.order_date > '2023-01-01'
    AND p.category = 'Electronics'
    AND u.status = 'active';

-- Scenario 2: CTE and INSERT operation with columns
WITH recent_orders AS (
    SELECT 
        customer_id,
        COUNT(*) as order_count,
        SUM(total_amount) as total_spent
    FROM 
        schema1.orders
    WHERE 
        order_date > CURRENT_DATE - INTERVAL '30 days'
    GROUP BY 
        customer_id
)
INSERT INTO schema2.customer_metrics (customer_id, monthly_order_count, monthly_spend, last_updated)
SELECT 
    customer_id,
    order_count,
    total_spent,
    CURRENT_TIMESTAMP
FROM 
    recent_orders
WHERE 
    order_count > 0;

-- Scenario 3: TRUNCATE alone (should appear in both dependencies and outputs)
TRUNCATE TABLE schema2.audit_logs;

-- Scenario 4: TRUNCATE followed by population of specific columns
TRUNCATE TABLE schema2.daily_summary;

INSERT INTO schema2.daily_summary (date, total_orders, total_revenue, avg_order_value)
SELECT 
    CURRENT_DATE,
    COUNT(*),
    SUM(total_amount),
    AVG(total_amount)
FROM 
    schema1.orders
WHERE 
    order_date = CURRENT_DATE;

-- Scenario 5: UPDATE with subquery
UPDATE schema1.products
SET 
    stock_status = 
        CASE 
            WHEN current_stock = 0 THEN 'Out of Stock'
            WHEN current_stock < 10 THEN 'Low Stock'
            ELSE 'In Stock'
        END,
    last_updated = CURRENT_TIMESTAMP
WHERE 
    product_id IN (
        SELECT 
            product_id
        FROM 
            schema1.order_items
        WHERE 
            order_date > CURRENT_DATE - INTERVAL '7 days'
    );

-- Scenario 6: CREATE TABLE and immediate population
CREATE TABLE schema2.monthly_report AS
SELECT 
    DATE_TRUNC('month', o.order_date) AS month,
    p.category,
    COUNT(DISTINCT o.order_id) AS order_count,
    COUNT(DISTINCT o.user_id) AS customer_count,
    SUM(oi.quantity) AS total_items_sold,
    SUM(o.total_amount) AS total_revenue
FROM 
    schema1.orders o
JOIN 
    schema1.order_items oi ON o.order_id = oi.order_id
JOIN 
    schema1.products p ON oi.product_id = p.product_id
GROUP BY 
    DATE_TRUNC('month', o.order_date),
    p.category;

-- Scenario 7: SELECT * (should generate ["*"] in dependencies)
SELECT *
FROM schema1.users
WHERE registration_date > CURRENT_DATE - INTERVAL '90 days';