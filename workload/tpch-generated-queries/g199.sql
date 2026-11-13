-- generated TPC-H-schema training query (seed 7, #199, family spj_agg); not an official TPC-H query
SELECT p_partkey AS partkey,
       l_suppkey AS suppkey,
       COUNT(*) AS m0,
       SUM(l_quantity) AS m1,
       AVG(o_totalprice) AS m2
FROM partsupp, lineitem, part, orders, customer, supplier, nation
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND p_container LIKE 'WRAP%'
  AND n_name IN ('FRANCE', 'KENYA', 'CHINA')
GROUP BY p_partkey, l_suppkey
HAVING COUNT(*) > 5
ORDER BY m0 DESC, partkey, suppkey
LIMIT 100
