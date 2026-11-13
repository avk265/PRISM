-- generated TPC-H-schema training query (seed 7, #314, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       year(l_shipdate) AS ship_year,
       AVG(l_discount) AS m0,
       AVG(o_totalprice) AS m1
FROM lineitem, partsupp, orders
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_orderkey = o_orderkey
  AND ps_supplycost < 200
  AND l_receiptdate > l_commitdate
GROUP BY l_linestatus, year(l_shipdate)
ORDER BY m0 DESC, linestatus, ship_year
LIMIT 100
