-- generated TPC-H-schema training query (seed 7, #319, family distinct); not an official TPC-H query
SELECT l_shipmode AS shipmode, COUNT(DISTINCT l_partkey) AS m0
FROM lineitem
WHERE l_shipdate >= DATE '1995-01-01' AND l_shipdate < DATE '1993-01-01'
  AND l_shipmode IN ('REG AIR')
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
