-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_returnflag AS returnflag,
       AVG(l_discount) AS m0
FROM lineitem, orders, supplier, partsupp
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_supplycost < 50
  AND l_receiptdate > l_commitdate
GROUP BY l_returnflag
ORDER BY m0 DESC, returnflag
LIMIT 100
