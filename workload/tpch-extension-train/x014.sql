-- generated TPC-H-schema training query (seed 11, #14, family big_join); not an official TPC-H query
SELECT year(o_orderdate) AS yr, SUM(l_extendedprice * (1 - l_discount)) AS m0, COUNT(*) AS m1
FROM lineitem, orders, customer, nation
WHERE l_orderkey = o_orderkey
  AND o_custkey = c_custkey
  AND c_nationkey = n_nationkey
  AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1995-01-01'
  AND c_mktsegment = 'BUILDING'
GROUP BY year(o_orderdate)
ORDER BY m0 DESC, yr
LIMIT 100
