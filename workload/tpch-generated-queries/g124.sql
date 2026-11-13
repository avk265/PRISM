-- generated TPC-H-schema training query (seed 1007, replacement for a many-to-many join query, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0,
       COUNT(*) AS m1,
       SUM(o_totalprice) AS m2
FROM lineitem, orders, supplier, part
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = p_partkey
  AND l_returnflag = 'N'
  AND p_size IN (2, 46, 23, 42, 45, 5)
  AND s_acctbal > 0
