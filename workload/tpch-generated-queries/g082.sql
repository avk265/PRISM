-- generated TPC-H-schema training query (seed 7, #82, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       o_orderpriority AS orderpriority,
       SUM(l_quantity) AS m0,
       COUNT(DISTINCT o_custkey) AS m1,
       COUNT(*) AS m2
FROM lineitem, orders, partsupp, supplier, nation, part
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND ps_partkey = p_partkey
  AND s_acctbal > 0
  AND ps_supplycost < 50
GROUP BY o_orderstatus, o_orderpriority
ORDER BY m0 DESC, orderstatus, orderpriority
LIMIT 100
