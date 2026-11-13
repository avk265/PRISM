-- generated TPC-H-schema training query (seed 11, #63, family big_join); not an official TPC-H query
SELECT c_mktsegment AS seg, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_shipdate >= DATE '1993-01-01' AND l_shipdate < DATE '1999-01-01'
  AND l_returnflag = 'A'
GROUP BY c_mktsegment
ORDER BY m0 DESC, seg
LIMIT 100
