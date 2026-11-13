-- generated TPC-H-schema training query (seed 7, #274, family spj_agg); not an official TPC-H query
SELECT l_suppkey AS suppkey,
       SUM(l_quantity) AS m0,
       MAX(l_extendedprice) AS m1
FROM lineitem, supplier, partsupp, part
WHERE l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_partkey = p_partkey
  AND s_acctbal > 0
GROUP BY l_suppkey
ORDER BY m0 DESC, suppkey
LIMIT 100
