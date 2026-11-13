-- generated TPC-H-schema training query (seed 7, #177, family spj_agg); not an official TPC-H query
SELECT o_orderstatus AS orderstatus,
       MIN(ps_supplycost) AS m0,
       SUM(l_quantity) AS m1
FROM lineitem, orders, partsupp, supplier, nation, region, part
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND ps_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND n_regionkey = r_regionkey
  AND l_partkey = p_partkey
GROUP BY o_orderstatus
ORDER BY m0 DESC, orderstatus
LIMIT 100
