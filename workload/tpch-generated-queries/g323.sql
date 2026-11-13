-- generated TPC-H-schema training query (seed 7, #323, family spj_agg); not an official TPC-H query
SELECT year(l_shipdate) AS ship_year,
       l_linestatus AS linestatus,
       SUM(l_quantity) AS m0
FROM lineitem, orders, partsupp
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_shipmode IN ('AIR', 'SHIP', 'REG AIR')
  AND ps_supplycost < 200
  AND o_orderpriority IN ('5-LOW')
GROUP BY year(l_shipdate), l_linestatus
ORDER BY m0 DESC, ship_year, linestatus
LIMIT 100
