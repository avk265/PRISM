-- generated TPC-H-schema training query (seed 7, #317, family distinct); not an official TPC-H query
SELECT l_shipmode AS shipmode, COUNT(DISTINCT l_partkey) AS m0
FROM lineitem
WHERE l_returnflag = 'A'
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
