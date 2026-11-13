-- generated TPC-H-schema training query (seed 11, #65, family scan_agg); not an official TPC-H query
SELECT l_returnflag AS rf, SUM(l_quantity) AS m0
FROM lineitem
WHERE l_returnflag = 'N'
  AND l_discount BETWEEN 0.02 AND 0.1
GROUP BY l_returnflag
ORDER BY rf
