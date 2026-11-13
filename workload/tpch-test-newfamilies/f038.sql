-- generated TPC-H-schema test-only query (seed 23, #38, family rollup); not an official TPC-H query
SELECT year(o_orderdate) AS yr, l_shipmode AS sm, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND l_receiptdate > l_commitdate
GROUP BY ROLLUP(year(o_orderdate), l_shipmode)
ORDER BY yr NULLS FIRST, sm NULLS FIRST
