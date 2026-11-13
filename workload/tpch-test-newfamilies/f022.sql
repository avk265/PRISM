-- generated TPC-H-schema test-only query (seed 23, #22, family rollup); not an official TPC-H query
SELECT l_shipmode AS sm, o_orderpriority AS op, SUM(l_extendedprice) AS m0, COUNT(*) AS m1
FROM lineitem, orders
WHERE l_orderkey = o_orderkey
  AND l_discount BETWEEN 0.0 AND 0.06
GROUP BY CUBE(l_shipmode, o_orderpriority)
ORDER BY sm NULLS FIRST, op NULLS FIRST
