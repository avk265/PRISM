-- generated TPC-H-schema test-only query (seed 23, #30, family rollup); not an official TPC-H query
SELECT o_orderpriority AS op, year(o_orderdate) AS yr, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
GROUP BY ROLLUP(o_orderpriority, year(o_orderdate))
ORDER BY op NULLS FIRST, yr NULLS FIRST
