-- generated TPC-H-schema test-only query (seed 23, #7, family rollup); not an official TPC-H query
SELECT l_returnflag AS rf, l_shipmode AS sm, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
GROUP BY ROLLUP(l_returnflag, l_shipmode)
ORDER BY rf NULLS FIRST, sm NULLS FIRST
