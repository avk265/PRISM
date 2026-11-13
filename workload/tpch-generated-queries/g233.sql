-- generated TPC-H-schema training query (seed 7, #233, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       l_shipmode AS shipmode,
       SUM(l_quantity) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1
FROM lineitem
GROUP BY l_linestatus, l_shipmode
HAVING COUNT(*) > 20
ORDER BY m0 DESC, linestatus, shipmode
LIMIT 100
