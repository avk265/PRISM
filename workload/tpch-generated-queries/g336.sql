-- generated TPC-H-schema training query (seed 7, #336, family spj_agg); not an official TPC-H query
SELECT MAX(l_extendedprice) AS m0,
       SUM(l_quantity) AS m1
FROM lineitem, supplier, nation, part
WHERE l_suppkey = s_suppkey
  AND s_nationkey = n_nationkey
  AND l_partkey = p_partkey
  AND s_acctbal > 0
  AND l_returnflag = 'N'
