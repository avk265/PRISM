-- generated TPC-H-schema training query (seed 7, #303, family spj_agg); not an official TPC-H query
SELECT o_custkey AS custkey,
       COUNT(*) AS m0
FROM lineitem, partsupp, part, orders
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_partkey = p_partkey
  AND l_orderkey = o_orderkey
GROUP BY o_custkey
HAVING COUNT(*) > 1
ORDER BY m0 DESC, custkey
LIMIT 100
