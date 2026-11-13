-- generated TPC-H-schema training query (seed 7, #292, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       l_shipmode AS shipmode,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       AVG(l_discount) AS m1
FROM lineitem
WHERE l_discount BETWEEN 0.02 AND 0.06
GROUP BY l_linestatus, l_shipmode
ORDER BY m0 DESC, linestatus, shipmode
LIMIT 100
