-- generated TPC-H-schema training query (seed 11, #93, family big_join); not an official TPC-H query
SELECT o_custkey AS ck, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01'
  AND c_mktsegment = 'HOUSEHOLD'
GROUP BY o_custkey
ORDER BY m0 DESC, ck
LIMIT 100
