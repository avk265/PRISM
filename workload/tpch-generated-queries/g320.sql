-- generated TPC-H-schema training query (seed 7, #320, family spj_agg); not an official TPC-H query
SELECT o_custkey AS custkey,
       l_linestatus AS linestatus,
       COUNT(*) AS m0,
       AVG(o_totalprice) AS m1
FROM lineitem, partsupp, orders, part
WHERE l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_orderkey = o_orderkey
  AND l_partkey = p_partkey
GROUP BY o_custkey, l_linestatus
ORDER BY m0 DESC, custkey, linestatus
LIMIT 100
