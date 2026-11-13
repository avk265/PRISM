-- generated TPC-H-schema training query (seed 11, #96, family scan_agg); not an official TPC-H query
SELECT l_returnflag AS rf, COUNT(*) AS m0, SUM(l_quantity) AS m1
FROM lineitem
WHERE l_quantity < 15
  AND l_discount BETWEEN 0.05 AND 0.1
GROUP BY l_returnflag
ORDER BY rf
