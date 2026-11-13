-- generated TPC-H-schema training query (seed 7, #62, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0,
       MAX(l_extendedprice) AS m1,
       SUM(s_acctbal) AS m2
FROM customer, orders, lineitem, supplier
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey IN (SELECT p_partkey FROM part WHERE p_size < 15)
