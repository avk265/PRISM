-- generated TPC-H-schema training query (seed 7, #17, family spj_agg); not an official TPC-H query
SELECT l_linestatus AS linestatus,
       COUNT(*) AS m0
FROM lineitem, part, orders
WHERE l_partkey = p_partkey
  AND l_orderkey = o_orderkey
GROUP BY l_linestatus
ORDER BY m0 DESC, linestatus
LIMIT 100
