-- generated TPC-H-schema training query (seed 7, #88, family spj_agg); not an official TPC-H query
SELECT o_orderpriority AS orderpriority,
       p_type AS ptype,
       SUM(l_quantity) AS m0
FROM orders, customer, lineitem, part, nation, supplier
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND c_nationkey = n_nationkey
  AND l_suppkey = s_suppkey
GROUP BY o_orderpriority, p_type
HAVING COUNT(*) > 20
ORDER BY m0 DESC, orderpriority, ptype
LIMIT 100
