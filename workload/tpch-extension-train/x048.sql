-- generated TPC-H-schema training query (seed 11, #48, family big_join); not an official TPC-H query
SELECT l_orderkey AS ok, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_mktsegment = 'AUTOMOBILE'
GROUP BY l_orderkey
ORDER BY m0 DESC, ok
LIMIT 100
