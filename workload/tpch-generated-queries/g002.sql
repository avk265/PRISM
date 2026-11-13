-- generated TPC-H-schema training query (seed 7, #2, family spj_agg); not an official TPC-H query
SELECT SUM(l_quantity) AS m0,
       AVG(l_discount) AS m1,
       SUM(o_totalprice) AS m2
FROM orders, customer, lineitem, nation
WHERE o_custkey = c_custkey
  AND l_orderkey = o_orderkey
  AND c_nationkey = n_nationkey
  AND c_acctbal > -500
