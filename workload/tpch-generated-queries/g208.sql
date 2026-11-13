-- generated TPC-H-schema training query (seed 7, #208, family spj_agg); not an official TPC-H query
SELECT p_size AS psize,
       MIN(ps_supplycost) AS m0,
       COUNT(*) AS m1,
       SUM(l_quantity) AS m2
FROM partsupp, part, lineitem, supplier, orders, customer, nation
WHERE ps_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_suppkey = s_suppkey
  AND l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND s_nationkey = n_nationkey
  AND l_discount BETWEEN 0.0 AND 0.06
GROUP BY p_size
HAVING COUNT(*) > 5
ORDER BY m0 DESC, psize
LIMIT 100
