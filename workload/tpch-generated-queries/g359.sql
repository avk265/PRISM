-- generated TPC-H-schema training query (seed 7, #359, family spj_agg); not an official TPC-H query
SELECT o_custkey AS custkey,
       SUM(o_totalprice) AS m0,
       SUM(c_acctbal) AS m1
FROM orders, lineitem, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
GROUP BY o_custkey
ORDER BY m0 DESC, custkey
LIMIT 100
