-- generated TPC-H-schema training query (seed 11, #41, family scan_agg); not an official TPC-H query
SELECT SUM(l_quantity) AS m0, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m1, SUM(l_extendedprice * l_discount) AS m2
FROM lineitem
WHERE l_returnflag = 'N'
