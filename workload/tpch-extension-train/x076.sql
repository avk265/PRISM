-- generated TPC-H-schema training query (seed 11, #76, family big_join); not an official TPC-H query
SELECT c_mktsegment AS seg, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND o_orderdate >= DATE '1997-01-01' AND o_orderdate < DATE '2000-01-01'
  AND c_mktsegment = 'HOUSEHOLD'
  AND l_shipmode IN ('RAIL')
GROUP BY c_mktsegment
ORDER BY m0 DESC, seg
LIMIT 100
