-- generated TPC-H-schema training query (seed 7, #289, family distinct); not an official TPC-H query
SELECT l_shipmode AS shipmode, COUNT(DISTINCT l_suppkey) AS m0
FROM lineitem
WHERE l_shipmode IN ('SHIP', 'FOB', 'RAIL', 'AIR')
  AND l_discount BETWEEN 0.05 AND 0.06
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
