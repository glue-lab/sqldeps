-- Postgres Function
CREATE OR REPLACE FUNCTION web_import."build_Api_Property_Defor"()
 RETURNS void
 LANGUAGE plpgsql
AS $function$BEGIN
	TRUNCATE TABLE web_import."Api_Property_Defor";

INSERT INTO web_import."Api_Property_Defor"(
		"PropertyId", "Year", "Ha"
	)
	SELECT ps."PropertyId", d."Year", avg("Defor") AS "Ha"
FROM build_public."Property_Shape" ps
INNER JOIN (
				SELECT "ShapeId", "Year"::INTEGER, SUM("areaha") AS "Defor"
FROM build_spatial."Shape_Defor"
WHERE "Year"::text ~ '^[0-9]+$'
-- and "areaha">6.25
GROUP BY "ShapeId", "Year"::INTEGER
			) d
				ON
d."ShapeId" = ps."ShapeId"
WHERE ps."PropertyId" IS NOT NULL
GROUP BY ps."PropertyId", d."Year";

END
$function$