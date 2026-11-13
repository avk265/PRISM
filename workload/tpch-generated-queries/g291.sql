-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       COUNT(DISTINCT o_custkey) AS m0,
       SUM(l_quantity) AS m1
FROM lineitem, orders, partsupp, supplier, nation, region
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND s_acctbal > 0
GROUP BY l_suppkey
ORDER BY m0 DESC, suppkey
LIMIT 100
