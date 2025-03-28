-- Simple Subquery 2
SELECT 
    u.name, 
    uo.order_count
FROM users u
JOIN (
    SELECT 
        user_id, 
        COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
) uo ON u.id = uo.user_id;