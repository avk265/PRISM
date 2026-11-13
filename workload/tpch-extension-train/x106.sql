-- generated TPC-H-schema training query (seed 11, #106, family scan_agg); not an official TPC-H query
SELECT SUM(l_quantity) AS m0
FROM lineitem
WHERE l_returnflag = 'N'
