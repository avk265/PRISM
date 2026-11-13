-- generated TPC-H-schema training query (seed 11, #83, family scan_agg); not an official TPC-H query
SELECT l_returnflag AS rf, COUNT(*) AS m0, SUM(l_extendedprice * l_discount) AS m1
FROM lineitem
WHERE l_shipmode IN ('REG AIR')
  AND l_quantity < 40
  AND l_receiptdate > l_commitdate
GROUP BY l_returnflag
ORDER BY rf
