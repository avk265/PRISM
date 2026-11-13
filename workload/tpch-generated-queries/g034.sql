-- generated TPC-H-schema training query (seed 7, #34, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       SUM(s_acctbal) AS m0,
       COUNT(*) AS m1
FROM lineitem, partsupp, orders, supplier, part, customer
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND ps_partkey = p_partkey
  AND o_custkey = c_custkey
  AND p_container LIKE 'WRAP%'
GROUP BY p_size
HAVING COUNT(*) > 5
ORDER BY m0 DESC, psize
LIMIT 100
