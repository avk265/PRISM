-- generated TPC-H-schema training query (seed 11, #98, family big_join); not an official TPC-H query
SELECT o_custkey AS ck, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND o_orderdate >= DATE '1995-01-01' AND o_orderdate < DATE '2001-01-01'
  AND l_shipdate >= DATE '1993-01-01' AND l_shipdate < DATE '1999-01-01'
GROUP BY o_custkey
ORDER BY m0 DESC, ck
LIMIT 100
