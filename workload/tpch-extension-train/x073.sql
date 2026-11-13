-- generated TPC-H-schema training query (seed 11, #73, family scan_agg); not an official TPC-H query
SELECT l_linestatus AS ls, l_returnflag AS rf, SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS m0
FROM lineitem
WHERE l_returnflag = 'R'
  AND l_discount BETWEEN 0.02 AND 0.08
GROUP BY l_linestatus, l_returnflag
ORDER BY ls, rf
