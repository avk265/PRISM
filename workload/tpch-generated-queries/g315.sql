-- generated TPC-H-schema training query (seed 7, #315, family distinct); not an official TPC-H query
SELECT l_shipmode AS shipmode, COUNT(DISTINCT l_orderkey) AS m0
FROM lineitem
WHERE l_discount BETWEEN 0.02 AND 0.08
GROUP BY l_shipmode
ORDER BY m0 DESC, shipmode
