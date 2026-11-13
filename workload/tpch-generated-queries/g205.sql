-- generated TPC-H-schema training query (seed 7, #205, family distinct); not an official TPC-H query
SELECT l_shipmode AS shipmode, COUNT(DISTINCT l_partkey) AS m0
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_shipmode IN ('AIR')
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
