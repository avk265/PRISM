-- generated TPC-H-schema training query (seed 11, #26, family big_join); not an official TPC-H query
SELECT l_orderkey AS ok, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND l_shipdate >= DATE '1996-01-01' AND l_shipdate < DATE '1999-01-01'
  AND c_mktsegment = 'AUTOMOBILE'
  AND l_returnflag = 'R'
GROUP BY l_orderkey
ORDER BY m0 DESC, ok
LIMIT 100
