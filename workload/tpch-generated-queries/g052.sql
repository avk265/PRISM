-- generated TPC-H-schema training query (seed 7, #52, family spj_agg); not an official TPC-H query
SELECT SUM(l_quantity) AS m0
FROM lineitem, supplier, partsupp, orders
WHERE l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_orderkey = o_orderkey
