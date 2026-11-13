-- generated TPC-H-schema training query (seed 7, #77, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       l_returnflag AS returnflag,
       l_shipmode AS shipmode,
       MAX(l_extendedprice) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1
FROM lineitem
GROUP BY l_linestatus, l_returnflag, l_shipmode
ORDER BY m0 DESC, linestatus, returnflag, shipmode
LIMIT 100
