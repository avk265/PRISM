-- generated TPC-H-schema training query (seed 11, #37, family scan_agg); not an official TPC-H query
SELECT l_shipmode AS sm, COUNT(*) AS m0, AVG(l_extendedprice) AS m1
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_returnflag = 'N'
GROUP BY l_shipmode
ORDER BY sm
