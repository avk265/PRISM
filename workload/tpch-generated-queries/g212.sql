-- generated TPC-H-schema training query (seed 7, #212, family spj_agg); not an official TPC-H query
SELECT COUNT(*) AS m0,
       AVG(o_totalprice) AS m1
FROM lineitem, orders, supplier, part, customer
WHERE l_orderkey = o_orderkey
  AND l_suppkey = s_suppkey
  AND l_partkey = p_partkey
  AND o_custkey = c_custkey
  AND s_acctbal > -500
