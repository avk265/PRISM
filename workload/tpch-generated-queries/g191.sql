-- generated TPC-H-schema training query (seed 7, #191, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0,
       SUM(l_quantity) AS m1
FROM orders, customer, lineitem, part, partsupp
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND c_acctbal > 8000
