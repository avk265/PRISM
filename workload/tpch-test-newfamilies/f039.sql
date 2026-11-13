-- generated TPC-H-schema test-only query (seed 23, #39, family rollup); not an official TPC-H query
SELECT l_shipmode AS sm, l_returnflag AS rf, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND l_returnflag = 'A'
GROUP BY ROLLUP(l_shipmode, l_returnflag)
ORDER BY sm NULLS FIRST, rf NULLS FIRST
