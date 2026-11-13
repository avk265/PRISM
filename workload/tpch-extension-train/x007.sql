-- generated TPC-H-schema training query (seed 11, #7, family scan_agg); not an official TPC-H query
SELECT COUNT(*) AS m0
FROM lineitem
WHERE l_returnflag = 'A'
  AND l_receiptdate > l_commitdate
  AND l_shipdate >= DATE '1992-01-01' AND l_shipdate < DATE '1993-01-01'
