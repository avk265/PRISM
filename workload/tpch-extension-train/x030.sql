-- generated TPC-H-schema training query (seed 11, #30, family big_join); not an official TPC-H query
SELECT l_orderkey AS ok, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND l_shipmode IN ('RAIL', 'AIR', 'SHIP')
GROUP BY l_orderkey
ORDER BY m0 DESC, ok
LIMIT 100
