-- generated TPC-H-schema training query (seed 7, #254, family spj_agg); not an official TPC-H query
SELECT s_suppkey AS s_suppkey,
       c_mktsegment AS mktsegment,
       p_partkey AS partkey,
       COUNT(*) AS m0,
       SUM(ps_supplycost * ps_availqty) AS m1
FROM lineitem, orders, partsupp, customer, nation, supplier, part
WHERE l_orderkey = o_orderkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND l_suppkey = s_suppkey
  AND ps_partkey = p_partkey
  AND n_name IN ('BRAZIL', 'JAPAN')
GROUP BY s_suppkey, c_mktsegment, p_partkey
ORDER BY m0 DESC, s_suppkey, mktsegment, partkey
LIMIT 100
