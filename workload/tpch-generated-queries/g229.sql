-- generated TPC-H-schema training query (seed 7, #229, family spj_agg); not an official TPC-H query
SELECT AVG(o_totalprice) AS m0,
       AVG(l_discount) AS m1
FROM lineitem, supplier, partsupp, part, orders
WHERE l_suppkey = s_suppkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_partkey = p_partkey
  AND l_orderkey = o_orderkey
