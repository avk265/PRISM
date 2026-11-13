-- generated TPC-H-schema training query (seed 11, #81, family big_join); not an official TPC-H query
SELECT n_name AS nation, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND l_shipdate >= DATE '1996-01-01' AND l_shipdate < DATE '1999-01-01'
  AND c_acctbal > 8000
  AND l_quantity < 40
GROUP BY n_name
ORDER BY m0 DESC, nation
LIMIT 100
