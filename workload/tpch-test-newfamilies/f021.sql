-- generated TPC-H-schema test-only query (seed 23, #21, family rollup); not an official TPC-H query
SELECT year(o_orderdate) AS yr, o_orderpriority AS op, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND l_shipdate >= DATE '1995-01-01' AND l_shipdate < DATE '1997-01-01'
GROUP BY GROUPING SETS ((year(o_orderdate), o_orderpriority), (year(o_orderdate)), ())
ORDER BY yr NULLS FIRST, op NULLS FIRST
