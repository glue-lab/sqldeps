-- Query with table alias, with and without database specification, and join, and where clauses
SELECT u.id, u.name, o.order_id
FROM my_db.users u
JOIN orders AS o ON u.id = o.user_id
WHERE u.status = 'active'
    AND o.order_date >= '2024-01-01'
    AND o.total_amount > 100.00
    AND u.email LIKE '%@company.com'
    AND o.order_type IN ('retail', 'wholesale')
    AND (
        o.shipping_status = 'pending'
        OR (o.shipping_status = 'processed' AND o.priority_level = 'high')
    );