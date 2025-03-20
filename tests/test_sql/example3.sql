-- Query with table alias, with and without database specification, and join
SELECT u.id, u.name, o.order_id
FROM my_db.users u
JOIN orders AS o ON u.id = o.user_id