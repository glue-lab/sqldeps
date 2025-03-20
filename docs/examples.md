# Examples

Here are some practical examples of using SQLDeps for different use cases.

## Basic Dependency Extraction

### Example 1: Simple SELECT Query

```sql
-- example1.sql
SELECT u.id, u.name, o.order_id, o.amount
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
```

Extracted dependencies:

```json
{
  "dependencies": {
    "users": ["id", "name", "status"],
    "orders": ["order_id", "amount", "user_id"]
  },
  "outputs": {}
}
```

### Example 2: CTEs and Table Creation

```sql
-- example2.sql
WITH user_orders AS (
    SELECT o.user_id, COUNT(*) AS order_count
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE u.status = 'active'
    GROUP BY o.user_id
)

CREATE TABLE transactions.user_order_summary AS
SELECT * FROM user_orders;
```

Extracted dependencies:

```json
{
  "dependencies": {
    "orders": ["user_id"],
    "users": ["id", "status"]
  },
  "outputs": {
    "transactions.user_order_summary": ["*"]
  }
}
```

### Example 3: UPDATE Operation

```sql
-- example3.sql
UPDATE users
SET status = 'inactive'
WHERE last_login < CURRENT_DATE - INTERVAL '90 days'
AND status = 'active';
```

Extracted dependencies:

```json
{
  "dependencies": {
    "users": ["status", "last_login"]
  },
  "outputs": {
    "users": ["status"]
  }
}
```

### Example 4: INSERT Operation

```sql
-- example4.sql
INSERT INTO sales.order_summary (date, total_orders, total_amount)
SELECT 
    DATE_TRUNC('day', order_date) as date,
    COUNT(*) as total_orders,
    SUM(amount) as total_amount
FROM orders
GROUP BY DATE_TRUNC('day', order_date);
```

Extracted dependencies:

```json
{
  "dependencies": {
    "orders": ["order_date", "amount"],
    "sales.order_summary": ["date", "total_orders", "total_amount"]
  },
  "outputs": {
    "sales.order_summary": ["date", "total_orders", "total_amount"]
  }
}
```