-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT s_suppkey AS s_suppkey,
       SUM(c_acctbal) AS m0,
       COUNT(DISTINCT l_orderkey) AS m1,
       COUNT(*) AS m2
FROM lineitem, orders, supplier, partsupp, part, customer
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND o_custkey = c_custkey
GROUP BY s_suppkey
ORDER BY m0 DESC, s_suppkey
LIMIT 100
