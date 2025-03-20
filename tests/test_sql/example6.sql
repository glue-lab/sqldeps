-- Simple Subquery 1
SELECT 
    u.name, 
    (
        SELECT COUNT(*) 
        FROM orders o 
        WHERE o.user_id = u.id
        GROUP BY o.user_id
    ) as order_count
FROM users u;