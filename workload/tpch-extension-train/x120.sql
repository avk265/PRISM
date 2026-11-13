-- generated TPC-H-schema training query (seed 11, #120, family scan_agg); not an official TPC-H query
SELECT AVG(l_extendedprice) AS m0, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m1, COUNT(*) AS m2, SUM(l_quantity) AS m3
FROM lineitem
WHERE l_receiptdate > l_commitdate
  AND l_quantity < 40
  AND l_returnflag = 'N'
