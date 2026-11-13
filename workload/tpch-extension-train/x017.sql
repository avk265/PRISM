-- generated TPC-H-schema training query (seed 11, #17, family scan_agg); not an official TPC-H query
SELECT SUM(l_extendedprice * l_discount) AS m0, SUM(l_quantity) AS m1, AVG(l_extendedprice) AS m2, COUNT(*) AS m3
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_shipmode IN ('RAIL', 'TRUCK', 'MAIL', 'FOB')
  AND l_returnflag = 'A'
