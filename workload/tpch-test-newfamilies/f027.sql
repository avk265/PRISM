-- generated TPC-H-schema test-only query (seed 23, #27, family rollup); not an official TPC-H query
SELECT year(o_orderdate) AS yr, l_returnflag AS rf, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND l_quantity < 25
GROUP BY ROLLUP(year(o_orderdate), l_returnflag)
ORDER BY yr NULLS FIRST, rf NULLS FIRST
