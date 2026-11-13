-- generated TPC-H-schema training query (seed 7, #28, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       l_linestatus AS linestatus,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1,
       AVG(l_discount) AS m2
FROM lineitem, partsupp
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_availqty > 5000
  AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1997-01-01'
GROUP BY l_returnflag, l_linestatus
ORDER BY m0 DESC, returnflag, linestatus
LIMIT 100
