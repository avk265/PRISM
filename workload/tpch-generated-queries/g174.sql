-- generated TPC-H-schema training query (seed 7, #174, family distinct); not an official TPC-H query
SELECT l_shipmode AS shipmode, COUNT(DISTINCT l_suppkey) AS m0
FROM lineitem
WHERE l_shipmode IN ('MAIL', 'TRUCK', 'AIR', 'SHIP')
  AND l_quantity < 25
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
