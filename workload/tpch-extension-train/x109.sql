-- generated TPC-H-schema training query (seed 11, #109, family big_join); not an official TPC-H query
SELECT year(o_orderdate) AS yr, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_acctbal > 3000
  AND l_shipmode IN ('FOB')
GROUP BY year(o_orderdate)
ORDER BY m0 DESC, yr
LIMIT 100
