-- generated TPC-H-schema training query (seed 11, #110, family big_join); not an official TPC-H query
SELECT l_orderkey AS ok, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND o_orderdate >= DATE '1997-01-01' AND o_orderdate < DATE '1998-01-01'
  AND c_acctbal > 0
  AND l_discount BETWEEN 0.05 AND 0.08
GROUP BY l_orderkey
ORDER BY m0 DESC, ok
LIMIT 100
