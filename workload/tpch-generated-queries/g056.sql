-- generated TPC-H-schema training query (seed 7, #56, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       SUM(l_extendedprice * (1 - l_discount)) AS m0,
       SUM(l_quantity) AS m1,
       MIN(ps_supplycost) AS m2
FROM orders, lineitem, partsupp
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_availqty > 1000
  AND l_returnflag = 'A'
  AND o_orderpriority IN ('5-LOW', '1-URGENT', '2-HIGH')
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
LIMIT 100
