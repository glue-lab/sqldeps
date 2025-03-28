-- Multiple queries with CTEs & function
CREATE OR REPLACE FUNCTION make_pgi_shape_geom_clusters()
  RETURNS VOID
  LANGUAGE plpgsql
AS $function$
BEGIN

    -- Build table with cluster + geom data
    DROP TABLE IF EXISTS pgi_shape_geom_clusters CASCADE;
    CREATE TABLE pgi_shape_geom_clusters AS
        SELECT
            pgic."PropertyGroupId",
            pgic."ShapeGroupId",
            sh.geom,
            pgic."ShapeCluster" 
        FROM
            pgi_shape_clusters pgic
        LEFT JOIN
            spatial."Shape" sh
        ON
            pgic."PropertyGroupId" = sh."ShapeId";

    -- Integrity check: A Property observation should have at most one row
    ALTER TABLE pgi_shape_geom_clusters ADD PRIMARY KEY ("PropertyGroupId","ShapeGroupId");
    ANALYZE VERBOSE pgi_shape_geom_clusters;

END
$function$;

WITH user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM users u
JOIN user_orders uo ON u.id = uo.user_id;