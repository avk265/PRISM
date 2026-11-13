-- generated TPC-H-schema training query (seed 11, #1, family big_join); not an official TPC-H query
SELECT o_custkey AS ck, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_shipdate >= DATE '1996-01-01' AND l_shipdate < DATE '1999-01-01'
GROUP BY o_custkey
ORDER BY m0 DESC, ck
LIMIT 100
