-- generated TPC-H-schema training query (seed 7, #331, family spj_agg); not an official TPC-H query
SELECT p_partkey AS partkey,
       SUM(l_quantity) AS m0,
       COUNT(*) AS m1
FROM lineitem, orders, part, partsupp
WHERE l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
GROUP BY p_partkey
HAVING COUNT(*) > 5
ORDER BY m0 DESC, partkey
LIMIT 100
