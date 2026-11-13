-- generated TPC-H-schema training query (seed 7, #145, family spj_agg); not an official TPC-H query
SELECT SUM(o_totalprice) AS m0,
       AVG(p_retailprice) AS m1,
       SUM(l_extendedprice * (1 - l_discount)) AS m2
FROM orders, lineitem, part, customer, nation, partsupp, supplier
WHERE l_orderkey = o_orderkey
  AND l_partkey = p_partkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND l_partkey = ps_partkey AND l_suppkey = ps_suppkey
  AND l_suppkey = s_suppkey
  AND s_acctbal > 0
